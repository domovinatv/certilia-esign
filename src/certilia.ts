/**
 * Klijent za AKD Certilia eSign (ePotpis) i AdES (PAdES/XAdES) Web API.
 * Prema: "ePotpis — Tehnička specifikacija za integraciju pružatelja e-Usluga", v4.0.13.
 */
import type { Config, TsaAccess } from './config.js';

const HOSTS = {
  test: { esign: 'https://esign.test.certilia.com', api: 'https://api.test.certilia.com' },
  prod: { esign: 'https://esign.certilia.com', api: 'https://api.certilia.com' },
} as const;

export type SignatureType = 'sign' | 'seal';
export type SignatureLevel = 'b' | 't' | 'lt' | 'lta';

export interface InitResult {
  token: string;
  verificationCodes: string[];
  expireAt?: string;
}

export interface PreSignDocument {
  verificationCode: string;
  base64Document: string;
  documentName?: string;
  firstRowMessage?: string;
  secondRowMessage?: string;
  thirdRowMessage?: string;
  pageNumber?: number;
  pageLocation?: number;
}

export interface PreSignResult {
  token: string;
  documents: { hash: string; verificationCode: string; documentName?: string }[];
}

export interface SignedDocument {
  hash: string;
  signedHash: string;
  verificationCode: string;
}

export interface PostSignResult {
  token: string;
  documents: { verificationCode: string; base64Document: string; documentName?: string }[];
}

export class CertiliaError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body: unknown,
  ) {
    super(message);
    this.name = 'CertiliaError';
  }
}

async function request<T>(url: string, method: string, body: unknown, bearer?: string): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
    },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  let json: unknown;
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    json = { raw: text };
  }
  if (!res.ok) {
    const msg =
      (json as { error?: { message?: string; title?: string } })?.error?.message ??
      (json as { error?: { title?: string } })?.error?.title ??
      text.slice(0, 500);
    throw new CertiliaError(`${method} ${url} -> HTTP ${res.status}: ${msg}`, res.status, json);
  }
  return json as T;
}

export class CertiliaClient {
  private readonly esign: string;
  private readonly api: string;

  constructor(private readonly cfg: Config) {
    this.esign = HOSTS[cfg.env].esign;
    this.api = HOSTS[cfg.env].api;
  }

  /** 5.2.1 — Zaprimanje inicijalnih podataka: vraća jednokratni token i verifikacijske kodove. */
  async initTransaction(numOfDocs: number, signatureType: SignatureType, mimetype?: 'pdf' | 'xml'): Promise<InitResult> {
    const res = await request<{ authDataResponse: InitResult }>(`${this.esign}/api/v2/epotpis`, 'POST', {
      authData: {
        systemId: this.cfg.systemId,
        serviceId: this.cfg.serviceId,
        documentId: this.cfg.documentId,
      },
      signingData: {
        numOfDocs: String(numOfDocs),
        ...(mimetype ? { mimetype } : {}),
        signatureType,
      },
    });
    return res.authDataResponse;
  }

  /** 5.3.5.1.1 — PAdES PreSign: izračun hash vrijednosti PDF-a (+ opcionalni vizual). */
  async padesPreSign(params: {
    token: string;
    signatureType: SignatureType;
    documents: PreSignDocument[];
    addVisualData?: boolean;
    personNaturalData?: { PIN: string; PINCountry: string; nameSurname?: string };
    personLegalData?: { VAT: string; VATCountry: string; name?: string; sealName?: string };
    addBlankPageOptions?: { blankPageOption: 'ADD_AUTO_ON_NO_SIGNATURES' };
  }): Promise<PreSignResult> {
    return request<PreSignResult>(`${this.api}/pades/v2`, 'POST', {
      token: params.token,
      signatureFormat: 'pades',
      signatureType: params.signatureType,
      ...(params.addVisualData !== undefined ? { addVisualData: params.addVisualData } : {}),
      ...(params.personNaturalData ? { personNaturalData: params.personNaturalData } : {}),
      ...(params.personLegalData ? { personLegalData: params.personLegalData } : {}),
      ...(params.addBlankPageOptions ? { addBlankPageOptions: params.addBlankPageOptions } : {}),
      documents: params.documents,
    }, this.cfg.adesToken);
  }

  /** 5.2.2 — Zaprimanje hash-a dokumenta; mobileSign=true šalje zahtjev direktno u Certilia mobilnu app. */
  async submitHashes(params: {
    token: string;
    documents: { hash: string; verificationCode: string }[];
    mobileSign?: boolean;
  }): Promise<void> {
    await request(`${this.esign}/api/v2/epotpis/hash`, 'PATCH', {
      authData: { token: params.token },
      signingData: {
        documents: params.documents,
        ...(params.mobileSign
          ? { mobileSign: true, oib: this.cfg.oib, country: this.cfg.country }
          : {}),
      },
    });
  }

  /** 5.2.3 — URL na koji se preusmjerava korisnik za potpis u browseru. */
  signingUrl(token: string): string {
    return `${this.esign}/epotpis/?token=${encodeURIComponent(token)}`;
  }

  /** 5.3.5.1.2 — PAdES PostSign: ugradnja potpisane vrijednosti u PDF. */
  async padesPostSign(params: {
    token: string;
    signatureLevel: SignatureLevel;
    userCertificate: string;
    documents: SignedDocument[];
    tsaAccess?: TsaAccess;
  }): Promise<PostSignResult> {
    if (params.signatureLevel !== 'b' && !params.tsaAccess) {
      throw new Error(`Razina potpisa "${params.signatureLevel}" zahtijeva AKD TSA pristupne podatke (CERTILIA_TSA_*).`);
    }
    return request<PostSignResult>(`${this.api}/pades/v2`, 'PATCH', {
      token: params.token,
      signatureFormat: 'pades',
      signatureLevel: params.signatureLevel,
      userCertificate: params.userCertificate,
      ...(params.tsaAccess ? { tsaAccess: params.tsaAccess } : {}),
      documents: params.documents,
    }, this.cfg.adesToken);
  }
}
