import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

function loadDotEnv(path = resolve(process.cwd(), '.env')): void {
  if (!existsSync(path)) return;
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    const m = line.match(/^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (!m) continue;
    const [, key, raw] = m;
    if (key && process.env[key] === undefined) {
      process.env[key] = raw!.replace(/^(["'])(.*)\1$/, '$2');
    }
  }
}
loadDotEnv();

export interface TsaAccess {
  url: string;
  username: string;
  password: string;
}

export interface Config {
  env: 'test' | 'prod';
  systemId: string;
  serviceId: string;
  documentId: string;
  adesToken: string;
  oib?: string;
  nameSurname?: string;
  country: string;
  legal?: { name?: string; VAT: string; VATCountry: string; sealName?: string };
  tsa?: TsaAccess;
  port: number;
  publicBaseUrl?: string;
}

function required(name: string): string {
  const v = process.env[name];
  if (!v) {
    console.error(`Nedostaje obavezna env varijabla ${name} — kopiraj .env.example u .env i popuni je.`);
    process.exit(1);
  }
  return v;
}

export function loadConfig(): Config {
  const env = (process.env.CERTILIA_ENV ?? 'test') as Config['env'];
  if (env !== 'test' && env !== 'prod') {
    console.error(`CERTILIA_ENV mora biti "test" ili "prod", ne "${env}"`);
    process.exit(1);
  }
  const tsaUrl = process.env.CERTILIA_TSA_URL;
  const tsaUser = process.env.CERTILIA_TSA_USERNAME;
  const tsaPass = process.env.CERTILIA_TSA_PASSWORD;
  const vat = process.env.CERTILIA_LEGAL_VAT;
  return {
    env,
    systemId: required('CERTILIA_SYSTEM_ID'),
    serviceId: required('CERTILIA_SERVICE_ID'),
    documentId: required('CERTILIA_DOCUMENT_ID'),
    adesToken: required('CERTILIA_ADES_TOKEN'),
    oib: process.env.CERTILIA_OIB || undefined,
    nameSurname: process.env.CERTILIA_NAME_SURNAME || undefined,
    country: process.env.CERTILIA_COUNTRY || 'HR',
    legal: vat
      ? {
          name: process.env.CERTILIA_LEGAL_NAME || undefined,
          VAT: vat,
          VATCountry: process.env.CERTILIA_LEGAL_VAT_COUNTRY || 'HR',
          sealName: process.env.CERTILIA_SEAL_NAME || undefined,
        }
      : undefined,
    tsa: tsaUrl && tsaUser && tsaPass ? { url: tsaUrl, username: tsaUser, password: tsaPass } : undefined,
    port: Number(process.env.PORT ?? 3355),
    publicBaseUrl: process.env.PUBLIC_BASE_URL || undefined,
  };
}
