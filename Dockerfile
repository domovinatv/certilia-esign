# Multi-stage: builder kompajlira TS, runtime ima samo dist + poppler-utils
# (pdftoppm/pdftotext/pdfinfo za pametno pozicioniranje vizuala, pdfsig za validaciju).
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig.json tsconfig.build.json ./
COPY src ./src
RUN npm run build


FROM node:22-alpine AS runtime

RUN apk add --no-cache poppler-utils

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3355

# Nema runtime npm ovisnosti — server koristi samo Node built-ine.
COPY --from=builder /app/dist ./dist

EXPOSE 3355

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --spider -q http://localhost:3355/health || exit 1

CMD ["node", "dist/server.js"]
