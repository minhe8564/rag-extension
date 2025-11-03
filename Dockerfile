FROM node:22.10.0-alpine AS base

# pnpm 설치
RUN npm install -g pnpm
WORKDIR /app

# 의존성 파일만 먼저 복사 (레이어 캐싱 최적화)
COPY package.json pnpm-lock.yaml ./

# 의존성 설치
RUN pnpm install --frozen-lockfile || pnpm install

# 소스 코드 복사 (코드 변경 시에만 이 레이어가 재빌드됨)
COPY . .

FROM base AS builder

# 빌드 모드 전달. Jenkins에서 --build-arg MODE=development/production 로 넘길 수 있음
# 값이 비어있으면 Vite 기본값(production)으로 빌드
ARG MODE
RUN if [ -n "$MODE" ]; then \
      echo "Vite build mode=$MODE" && pnpm run build -- --mode "$MODE"; \
    else \
      echo "Vite build default (production)" && pnpm run build; \
    fi

# Nginx를 사용한 정적 파일 서빙
FROM nginx:alpine AS production

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]
