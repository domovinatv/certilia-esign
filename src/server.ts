import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { randomUUID } from 'node:crypto';
import { readFile, writeFile, mkdir, copyFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { basename, dirname, extname, join, resolve } from 'node:path';
import { loadConfig } from './config.js';
import { CertiliaClient, type SignatureLevel, type SignatureType } from './certilia.js';
import { createJob, getJob, getJobByToken, publicJobView, type Job } from './jobs.js';
import { pickVisualPlacement } from './visual.js';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const runCmd = promisify(execFile);

const cfg = loadConfig();
const certilia = new CertiliaClient(cfg);
const SIGNED_DIR = resolve(process.cwd(), 'data/signed');
const UPLOADS_DIR = resolve(process.cwd(), 'data/uploads');
// ePotpis payload limit je ~35MB; base64 napuhne ~33% pa je 64MB tijela dovoljno.
const MAX_BODY = 64 * 1024 * 1024;
const apiKey = process.env.API_KEY || process.env.LOCAL_API_KEY || undefined;

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((res, rej) => {
    let size = 0;
    const chunks: Buffer[] = [];
    req.on('data', (c: Buffer) => {
      size += c.length;
      if (size > MAX_BODY) {
        rej(new Error('Body too large'));
        req.destroy();
        return;
      }
      chunks.push(c);
    });
    req.on('end', () => res(Buffer.concat(chunks).toString('utf8')));
    req.on('error', rej);
  });
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  const data = JSON.stringify(body);
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(data);
}

function sendHtml(res: ServerResponse, status: number, title: string, message: string): void {
  res.writeHead(status, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(`<!doctype html><meta charset="utf-8"><title>${title}</title>
<body style="font-family:system-ui;display:grid;place-items:center;height:100vh;margin:0">
<div style="text-align:center"><h1>${title}</h1><p>${message}</p></div></body>`);
}

interface SignRequest {
  /** Lokalne putanje — samo kad CLI i server dijele disk (lokalni način rada). */
  files?: string[];
  /** Upload sadržaja — remote način rada (Coolify i sl.). */
  documents?: { name: string; base64: string }[];
  seal?: boolean;
  mobile?: boolean;
  visual?: boolean;
  level?: SignatureLevel;
  /** Stranica za vizual: 0 = zadnja (default); vidi Prilog A specifikacije. */
  page?: number;
  /** Lokacija vizuala na stranici: 0 = prva slobodna, 1-12 = mreža (A4 portrait: 2x6, 11 = dolje lijevo). */
  location?: number;
}

async function handleSignRequest(body: SignRequest): Promise<Job> {
  let files: string[];
  if (Array.isArray(body.documents) && body.documents.length > 0) {
    const dir = join(UPLOADS_DIR, randomUUID());
    await mkdir(dir, { recursive: true });
    files = [];
    for (const d of body.documents) {
      const name = basename(d.name || 'dokument.pdf');
      if (extname(name).toLowerCase() !== '.pdf') throw new Error(`Nije PDF: ${name}`);
      if (!d.base64) throw new Error(`Prazan sadržaj dokumenta: ${name}`);
      const path = join(dir, name);
      await writeFile(path, Buffer.from(d.base64, 'base64'));
      files.push(path);
    }
  } else if (Array.isArray(body.files) && body.files.length > 0) {
    files = body.files.map((f) => resolve(f));
    for (const f of files) {
      if (!existsSync(f)) throw new Error(`Datoteka ne postoji: ${f}`);
      if (extname(f).toLowerCase() !== '.pdf') throw new Error(`Nije PDF: ${f}`);
    }
  } else {
    throw new Error('Pošalji "documents" (name + base64) ili "files" (lokalne putanje).');
  }
  if (files.length > 1 && !body.mobile) {
    throw new Error('Potpis više dokumenata u jednoj transakciji moguć je isključivo udaljenim certifikatom (koristi --mobile).');
  }
  const signatureType: SignatureType = body.seal ? 'seal' : 'sign';
  const level: SignatureLevel = body.level ?? 'b';
  if (body.mobile && !cfg.oib) {
    throw new Error('mobileSign zahtijeva CERTILIA_OIB u .env (OIB potpisnika).');
  }
  if (body.visual && signatureType === 'sign' && !cfg.oib) {
    throw new Error('Vizual potpisa zahtijeva CERTILIA_OIB (personNaturalData.PIN).');
  }
  if (body.visual && signatureType === 'seal' && !cfg.legal) {
    throw new Error('Vizual pečata zahtijeva CERTILIA_LEGAL_VAT (personLegalData).');
  }

  // 1) Inicijalizacija transakcije -> token + verifikacijski kodovi
  const init = await certilia.initTransaction(files.length, signatureType);
  if (init.verificationCodes.length < files.length) {
    throw new Error(`ePotpis vratio ${init.verificationCodes.length} verifikacijskih kodova za ${files.length} dokumenata.`);
  }

  // 2) PreSign -> hash svakog dokumenta (+ opcionalni vizual)
  // Pozicija vizuala: eksplicitni --page/--location imaju prednost; inače se
  // stranica renderira i bira najniža PRAZNA ćelija mreže (Prilog A). Ako prazne
  // ćelije nema, 0/0 tjera ePotpis da doda praznu stranicu — nikad ne prekrivamo sadržaj.
  const placements = body.visual
    ? await Promise.all(
        files.map(async (path) => {
          if (body.page !== undefined && body.location !== undefined) {
            return { pageNumber: body.page, pageLocation: body.location, auto: false };
          }
          const signerName = signatureType === 'sign' ? cfg.nameSurname : cfg.legal?.sealName ?? cfg.legal?.name;
          const auto = await pickVisualPlacement(path, body.page, signerName);
          if (auto) {
            console.log(
              `Vizual za ${basename(path)}: stranica ${auto.pageNumber}, lokacija ${auto.pageLocation}` +
                ` (auto${auto.anchored ? ', uz potpisni blok' : ''})`,
            );
            return { pageNumber: auto.pageNumber, pageLocation: auto.pageLocation, auto: true };
          }
          console.log(`Vizual za ${basename(path)}: nema prazne ćelije -> nova prazna stranica na kraju (0/0)`);
          return { pageNumber: 0, pageLocation: 0, auto: true };
        }),
      )
    : [];
  const documents = await Promise.all(
    files.map(async (path, i) => ({
      verificationCode: init.verificationCodes[i]!,
      base64Document: (await readFile(path)).toString('base64'),
      documentName: basename(path),
      ...(body.visual ? { pageNumber: placements[i]!.pageNumber, pageLocation: placements[i]!.pageLocation } : {}),
    })),
  );
  const preSign = await certilia.padesPreSign({
    token: init.token,
    signatureType,
    documents,
    ...(body.visual
      ? {
          addVisualData: true,
          ...(signatureType === 'sign'
            ? { personNaturalData: { PIN: cfg.oib!, PINCountry: cfg.country, nameSurname: cfg.nameSurname } }
            : { personLegalData: cfg.legal! }),
        }
      : { addVisualData: false }),
  });

  // 3) Predaja hash-eva ePotpisu (mobileSign gura zahtjev direktno u Certilia mobilnu app)
  const hashByCode = new Map(preSign.documents.map((d) => [d.verificationCode, d.hash]));
  await certilia.submitHashes({
    token: init.token,
    documents: preSign.documents.map((d) => ({ hash: d.hash, verificationCode: d.verificationCode })),
    mobileSign: body.mobile ?? false,
  });

  return createJob({
    token: init.token,
    status: 'awaiting-signature',
    signatureType,
    signatureLevel: level,
    mobile: body.mobile ?? false,
    signUrl: body.mobile ? undefined : certilia.signingUrl(init.token),
    expireAt: init.expireAt,
    files: files.map((path, i) => {
      const code = init.verificationCodes[i]!;
      return {
        inputPath: path,
        outputPath: join(dirname(path), `${basename(path, extname(path))}-potpisan.pdf`),
        documentName: basename(path),
        verificationCode: code,
        hash: hashByCode.get(code),
        visualPlacement: body.visual ? placements[i] : undefined,
      };
    }),
  });
}

/** Mini dokazni paket: JSON pored potpisanog PDF-a s podacima transakcije i lokalnom validacijom (pdfsig). */
async function writeEvidence(job: Job, outputPath: string, verificationCode: string): Promise<void> {
  const file = job.files.find((f) => f.verificationCode === verificationCode);
  let validation: unknown = 'pdfsig nije dostupan';
  try {
    const { stdout } = await runCmd('pdfsig', [outputPath]);
    validation = Object.fromEntries(
      [...stdout.matchAll(/- ([^:]+): (.+)/g)].map((m) => [m[1]!.trim(), m[2]!.trim()]),
    );
  } catch (e) {
    if (e && typeof e === 'object' && 'stdout' in e) validation = String((e as { stdout: unknown }).stdout).slice(0, 400);
  }
  const evidence = {
    document: basename(outputPath),
    input: file?.inputPath,
    signedAt: new Date().toISOString(),
    signatureType: job.signatureType,
    signatureLevel: job.signatureLevel,
    verificationCode,
    transactionToken: job.token,
    visualPlacement: file?.visualPlacement,
    onlineVerification: 'https://esign.certilia.com/provjera',
    localValidation: validation,
  };
  const evidencePath = outputPath.replace(/\.pdf$/i, '.dokaz.json');
  await writeFile(evidencePath, JSON.stringify(evidence, null, 2));
  if (file) file.evidence = evidence;
}

/** 5.2.4 — AKD nakon potpisa POST-a potpisani hash + certifikat na ovaj endpoint. */
async function handleSignedCallback(raw: string, res: ServerResponse): Promise<void> {
  const body = JSON.parse(raw) as {
    authData?: { token?: string };
    signingData?: { userCertificate?: string; documents?: { hash?: string; signedHash?: string; verificationCode?: string }[] };
    error?: { token?: string; message?: string; errorId?: string };
  };

  // 5.2.4.2 — korisnik odbio potpisivanje putem mobilne aplikacije
  if (body.error) {
    const job = body.error.token ? getJobByToken(body.error.token) : undefined;
    if (job) {
      job.status = 'rejected';
      job.error = body.error.message ?? 'Korisnik je odbio potpisivanje.';
      console.log(`[job ${job.id}] potpisivanje odbijeno: ${job.error}`);
    } else {
      console.warn('Callback (odbijanje) za nepoznati token');
    }
    sendJson(res, 200, { signingDataResponse: { status: '200' } });
    return;
  }

  const token = body.authData?.token;
  const job = token ? getJobByToken(token) : undefined;
  if (!job || !token) {
    sendJson(res, 400, { error: { status: '400', code: 'UNKNOWN_TOKEN', title: 'Nepoznat token transakcije' } });
    return;
  }
  const userCertificate = body.signingData?.userCertificate;
  const docs = body.signingData?.documents ?? [];
  if (!userCertificate || docs.length === 0) {
    sendJson(res, 400, { error: { status: '400', code: 'BAD_PAYLOAD', title: 'Nedostaje userCertificate ili documents' } });
    return;
  }

  // AKD-u odmah potvrđujemo zaprimanje, ugradnja potpisa ide asinkrono.
  sendJson(res, 201, { signingDataResponse: { status: '201' } });
  job.status = 'embedding';
  console.log(`[job ${job.id}] zaprimljen potpisani hash za ${docs.length} dokument(a), ugrađujem potpis...`);

  try {
    const signedByCode = new Map(docs.map((d) => [d.verificationCode, d]));
    const post = await certilia.padesPostSign({
      token,
      signatureLevel: job.signatureLevel,
      userCertificate,
      tsaAccess: job.signatureLevel === 'b' ? undefined : cfg.tsa,
      documents: job.files.map((f) => {
        const d = signedByCode.get(f.verificationCode);
        if (!d?.signedHash) throw new Error(`Nema signedHash za verificationCode ${f.verificationCode}`);
        return { verificationCode: f.verificationCode, hash: d.hash ?? f.hash!, signedHash: d.signedHash };
      }),
    });

    await mkdir(SIGNED_DIR, { recursive: true });
    for (const doc of post.documents) {
      const file = job.files.find((f) => f.verificationCode === doc.verificationCode);
      if (!file) continue;
      const buf = Buffer.from(doc.base64Document, 'base64');
      await writeFile(file.outputPath, buf);
      // Kopija pod verifikacijskim kodom — služi "Base download URL" dohvatu kod verifikacije.
      await copyFile(file.outputPath, join(SIGNED_DIR, `${doc.verificationCode}.pdf`));
      await writeEvidence(job, file.outputPath, file.verificationCode);
      console.log(`[job ${job.id}] potpisan: ${file.outputPath}`);
    }
    job.status = 'completed';
  } catch (err) {
    job.status = 'error';
    job.error = err instanceof Error ? err.message : String(err);
    console.error(`[job ${job.id}] greška kod ugradnje potpisa:`, job.error);
  }
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', 'http://localhost');
  const path = url.pathname;
  try {
    if (req.method === 'GET' && path === '/health') {
      sendJson(res, 200, { ok: true, env: cfg.env });
      return;
    }
    if (path.startsWith('/api/') && apiKey && req.headers['x-api-key'] !== apiKey) {
      sendJson(res, 401, { error: 'Neispravan ili nedostajući X-Api-Key' });
      return;
    }
    if (req.method === 'POST' && path === '/api/sign') {
      const job = await handleSignRequest(JSON.parse(await readBody(req)) as SignRequest);
      console.log(
        `[job ${job.id}] transakcija kreirana (${job.files.length} dok., ${job.signatureType}/${job.signatureLevel})` +
          (job.mobile ? ' -> čeka potvrdu u Certilia mobilnoj aplikaciji' : ` -> potpis na: ${job.signUrl}`),
      );
      sendJson(res, 201, publicJobView(job));
      return;
    }
    const download = path.match(/^\/api\/jobs\/([^/]+)\/download\/([0-9a-f-]+)$/);
    if (req.method === 'GET' && download) {
      const job = getJob(download[1]!);
      const file = job?.files.find((f) => f.verificationCode === download[2]);
      if (!job || !file) return sendJson(res, 404, { error: 'Nepoznat job ili dokument' });
      if (job.status !== 'completed') return sendJson(res, 409, { error: `Job još nije završen (${job.status})` });
      res.writeHead(200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${basename(file.outputPath)}"`,
      });
      res.end(await readFile(file.outputPath));
      return;
    }
    if (req.method === 'GET' && path.startsWith('/api/jobs/')) {
      const job = getJob(path.slice('/api/jobs/'.length));
      if (!job) return sendJson(res, 404, { error: 'Nepoznat job' });
      sendJson(res, 200, publicJobView(job));
      return;
    }
    if (req.method === 'POST' && path === '/esign/signed-pdf') {
      await handleSignedCallback(await readBody(req), res);
      return;
    }
    if (req.method === 'GET' && path === '/esign/success') {
      const token = url.searchParams.get('token') ?? undefined;
      const job = token ? getJobByToken(token) : undefined;
      sendHtml(res, 200, 'Potpisivanje uspješno ✅', job ? `Dokumenti: ${job.files.map((f) => f.documentName).join(', ')}` : 'Možete zatvoriti ovaj prozor.');
      return;
    }
    if (req.method === 'GET' && path === '/esign/error') {
      const token = url.searchParams.get('token') ?? undefined;
      const job = token ? getJobByToken(token) : undefined;
      if (job && job.status === 'awaiting-signature') {
        job.status = 'rejected';
        job.error = 'Preusmjereno na error URL s ePotpis stranice.';
      }
      sendHtml(res, 200, 'Potpisivanje nije uspjelo ❌', 'Pokušajte ponovno ili provjerite log servisa.');
      return;
    }
    if (req.method === 'GET' && /^\/esign\/docs\/[0-9a-f-]+\.pdf$/.test(path)) {
      const file = join(SIGNED_DIR, basename(path));
      if (!existsSync(file)) return sendJson(res, 404, { error: 'Ne postoji' });
      res.writeHead(200, { 'Content-Type': 'application/pdf' });
      res.end(await readFile(file));
      return;
    }
    if (req.method === 'GET' && path === '/') {
      sendHtml(res, 200, 'certilia-esign', `Lokalni servis za Certilia eSign potpisivanje (okolina: ${cfg.env}).`);
      return;
    }
    sendJson(res, 404, { error: 'Not found' });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`${req.method} ${path} greška:`, msg);
    sendJson(res, 500, { error: msg });
  }
});

server.listen(cfg.port, () => {
  console.log(`certilia-esign server sluša na http://localhost:${cfg.port} (okolina: ${cfg.env})`);
  if (cfg.publicBaseUrl) {
    console.log(`Javni URL: ${cfg.publicBaseUrl}`);
    console.log(`  Sign PDF URL:      ${cfg.publicBaseUrl}/esign/signed-pdf`);
    console.log(`  Success URL:       ${cfg.publicBaseUrl}/esign/success`);
    console.log(`  Error URL:         ${cfg.publicBaseUrl}/esign/error`);
    console.log(`  Base download URL: ${cfg.publicBaseUrl}/esign/docs/`);
  } else {
    console.log('PUBLIC_BASE_URL nije postavljen — pokreni cloudflared tunel i upiši URL u .env (vidi README).');
  }
  if (!apiKey) {
    console.warn('UPOZORENJE: API_KEY nije postavljen — /api/* rute su nezaštićene. Za javni deployment postavi API_KEY.');
  }
});
