/**
 * CLI za potpisivanje PDF-ova preko lokalnog certilia-esign servera.
 *
 *   npm run sign -- <putanja.pdf> [još.pdf ...] [opcije]
 *
 * Opcije:
 *   --mobile        potpis potvrđuješ u Certilia mobilnoj aplikaciji (bez browsera)
 *   --seal          pečat (seal) umjesto potpisa (sign)
 *   --visual        ugradi vizualni element potpisa u PDF
 *   --level <b|t|lt|lta>  razina potpisa (default: b; t+ traži TSA pristup)
 *   --page <n>      stranica za vizual (default 0 = zadnja; uz --visual)
 *   --location <n>  pozicija vizuala 0-12 (0 = prva slobodna; A4 portrait 2x6: 11 = dolje lijevo, 12 = dolje desno)
 *   --server <url>  URL lokalnog servera (default: http://localhost:3355)
 */
import { resolve } from 'node:path';

interface JobView {
  id: string;
  status: string;
  signUrl?: string;
  files: { input: string; output?: string }[];
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
    console.error('Uporaba: npm run sign -- <putanja.pdf> [još.pdf ...] [--mobile] [--seal] [--visual] [--level b|t|lt|lta]');
    process.exit(2);
  }
  return { files, opts };
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const { files, opts } = parseArgs(process.argv.slice(2));
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (process.env.LOCAL_API_KEY) headers['X-Api-Key'] = process.env.LOCAL_API_KEY;

  let res: Response;
  try {
    res = await fetch(`${opts.server}/api/sign`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        files,
        mobile: opts.mobile,
        seal: opts.seal,
        visual: opts.visual,
        level: opts.level,
        page: opts.page,
        location: opts.location,
      }),
    });
  } catch {
    console.error(`Server nije dostupan na ${opts.server} — pokreni ga s: npm run server`);
    process.exit(1);
  }
  const job = (await res.json()) as JobView & { error?: string };
  if (!res.ok) {
    console.error(`Greška: ${job.error ?? JSON.stringify(job)}`);
    process.exit(1);
  }

  console.log(`Transakcija kreirana (job ${job.id}).`);
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
      console.log('\n✅ Potpisano:');
      for (const f of j.files) console.log(`   ${f.output}`);
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
