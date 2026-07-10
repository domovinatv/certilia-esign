/**
 * CLI za potpisivanje PDF-ova preko certilia-esign servera (lokalnog ili remote).
 * Dokumenti se UPLOADAJU (base64), a potpisani PDF + dokaz.json se skidaju
 * natrag pored originala — radi identično prema localhost i prema
 * https://esign.domovina.ai deploymentu.
 *
 *   npm run sign -- <putanja.pdf> [još.pdf ...] [opcije]
 *
 * Opcije:
 *   --mobile        potpis potvrđuješ u Certilia mobilnoj aplikaciji (bez browsera)
 *   --seal          pečat (seal) umjesto potpisa (sign)
 *   --visual        ugradi vizualni element potpisa u PDF (pozicija automatska)
 *   --level <b|t|lt|lta>  razina potpisa (default: b; t+ traži TSA pristup)
 *   --page <n>      stranica za vizual (default 0 = zadnja; uz --visual)
 *   --location <n>  pozicija vizuala 0-12 (0 = prva slobodna; A4 portrait 2x6: 11 = dolje lijevo, 12 = dolje desno)
 *   --server <url>  URL servera (default: $CERTILIA_ESIGN_SERVER ili http://localhost:3355)
 *
 * Env: CERTILIA_ESIGN_SERVER, API_KEY (X-Api-Key header).
 */
import { readFile, writeFile } from 'node:fs/promises';
import { basename, dirname, extname, join, resolve } from 'node:path';

interface JobFileView {
  input: string;
  documentName: string;
  verificationCode: string;
  downloadPath?: string;
  evidence?: unknown;
}

interface JobView {
  id: string;
  status: string;
  signUrl?: string;
  files: JobFileView[];
  error?: string;
}

function parseArgs(argv: string[]) {
  const files: string[] = [];
  const opts = {
    mobile: false,
    seal: false,
    visual: false,
    level: 'b',
    page: undefined as number | undefined,
    location: undefined as number | undefined,
    server: process.env.CERTILIA_ESIGN_SERVER ?? 'http://localhost:3355',
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]!;
    if (a === '--mobile') opts.mobile = true;
    else if (a === '--seal') opts.seal = true;
    else if (a === '--visual') opts.visual = true;
    else if (a === '--level') opts.level = argv[++i] ?? 'b';
    else if (a === '--page') opts.page = Number(argv[++i]);
    else if (a === '--location') opts.location = Number(argv[++i]);
    else if (a === '--server') opts.server = argv[++i] ?? opts.server;
    else if (a.startsWith('--')) {
      console.error(`Nepoznata opcija: ${a}`);
      process.exit(2);
    } else files.push(resolve(a));
  }
  if (files.length === 0) {
    console.error('Uporaba: npm run sign -- <putanja.pdf> [još.pdf ...] [--mobile] [--seal] [--visual] [--level b|t|lt|lta] [--page N] [--location 0-12] [--server url]');
    process.exit(2);
  }
  opts.server = opts.server.replace(/\/+$/, '');
  return { files, opts };
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const { files, opts } = parseArgs(process.argv.slice(2));
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (process.env.API_KEY || process.env.LOCAL_API_KEY) {
    headers['X-Api-Key'] = (process.env.API_KEY ?? process.env.LOCAL_API_KEY)!;
  }

  const documents = await Promise.all(
    files.map(async (path) => ({
      name: basename(path),
      base64: (await readFile(path)).toString('base64'),
    })),
  );

  let res: Response;
  try {
    res = await fetch(`${opts.server}/api/sign`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        documents,
        mobile: opts.mobile,
        seal: opts.seal,
        visual: opts.visual,
        level: opts.level,
        page: opts.page,
        location: opts.location,
      }),
    });
  } catch {
    console.error(`Server nije dostupan na ${opts.server} — pokreni ga s: npm run server (ili provjeri --server URL).`);
    process.exit(1);
  }
  const job = (await res.json()) as JobView & { error?: string };
  if (!res.ok) {
    console.error(`Greška: ${job.error ?? JSON.stringify(job)}`);
    process.exit(1);
  }

  console.log(`Transakcija kreirana (job ${job.id}) na ${opts.server}.`);
  if (opts.mobile) {
    console.log('📱 Otvori Certilia aplikaciju na mobitelu i potvrdi potpisivanje.');
  } else {
    console.log(`🌐 Otvori u browseru i potpiši:\n\n   ${job.signUrl}\n`);
  }

  process.stdout.write('Čekam potpis');
  for (;;) {
    await sleep(2500);
    const s = await fetch(`${opts.server}/api/jobs/${job.id}`, { headers });
    const j = (await s.json()) as JobView;
    if (j.status === 'completed') {
      console.log('\n✅ Potpisano, skidam dokumente:');
      for (const f of j.files) {
        const src = files.find((p) => basename(p) === f.documentName) ?? files[0]!;
        const outPdf = join(dirname(src), `${basename(src, extname(src))}-potpisan.pdf`);
        const dl = await fetch(`${opts.server}${f.downloadPath}`, { headers });
        if (!dl.ok) {
          console.error(`   ⚠️  Download nije uspio za ${f.documentName}: HTTP ${dl.status}`);
          continue;
        }
        await writeFile(outPdf, Buffer.from(await dl.arrayBuffer()));
        console.log(`   ${outPdf}`);
        if (f.evidence) {
          const outEvidence = outPdf.replace(/\.pdf$/i, '.dokaz.json');
          await writeFile(outEvidence, JSON.stringify(f.evidence, null, 2));
          console.log(`   ${outEvidence}`);
        }
      }
      return;
    }
    if (j.status === 'rejected' || j.status === 'error') {
      console.error(`\n❌ ${j.status === 'rejected' ? 'Potpisivanje odbijeno' : 'Greška'}: ${j.error ?? ''}`);
      process.exit(1);
    }
    process.stdout.write('.');
  }
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
