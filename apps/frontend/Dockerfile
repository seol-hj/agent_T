# Frontend Dockerfile (Next.js 14)

FROM node:20-alpine AS base

# 의존성 설치
FROM base AS deps
WORKDIR /app

COPY package.json ./
RUN npm install

# 빌드
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . ./

# public 디렉토리가 없으면 생성
RUN mkdir -p ./public

RUN npm run build

# 실행
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=development

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
