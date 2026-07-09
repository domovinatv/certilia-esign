import { randomUUID } from 'node:crypto';
import type { SignatureLevel, SignatureType } from './certilia.js';

export type JobStatus = 'awaiting-signature' | 'embedding' | 'completed' | 'rejected' | 'error';

export interface JobFile {
  inputPath: string;
  outputPath: string;
  documentName: string;
  verificationCode: string;
  hash?: string;
  visualPlacement?: { pageNumber: number; pageLocation: number; auto: boolean };
}

export interface Job {
  id: string;
  token: string;
  status: JobStatus;
  signatureType: SignatureType;
  signatureLevel: SignatureLevel;
  mobile: boolean;
  signUrl?: string;
  files: JobFile[];
  error?: string;
  createdAt: string;
  expireAt?: string;
}

const byId = new Map<string, Job>();
const byToken = new Map<string, Job>();

export function createJob(job: Omit<Job, 'id' | 'createdAt'>): Job {
  const full: Job = { ...job, id: randomUUID(), createdAt: new Date().toISOString() };
  byId.set(full.id, full);
  byToken.set(full.token, full);
  return full;
}

export function getJob(id: string): Job | undefined {
  return byId.get(id);
}

export function getJobByToken(token: string): Job | undefined {
  return byToken.get(token);
}

export function publicJobView(job: Job) {
  return {
    id: job.id,
    status: job.status,
    signatureType: job.signatureType,
    signatureLevel: job.signatureLevel,
    mobile: job.mobile,
    signUrl: job.signUrl,
    files: job.files.map((f) => ({
      input: f.inputPath,
      output: job.status === 'completed' ? f.outputPath : undefined,
      documentName: f.documentName,
      verificationCode: f.verificationCode,
    })),
    error: job.error,
    createdAt: job.createdAt,
    expireAt: job.expireAt,
  };
}
