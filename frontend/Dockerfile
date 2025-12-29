# Base image with pnpm enabled
FROM node:22-alpine AS base
RUN corepack enable
WORKDIR /app

# Install dependencies (include dev deps for build)
FROM base AS deps
ARG NUXT_PUBLIC_API_BASE_URL
ENV NUXT_PUBLIC_API_BASE_URL=${NUXT_PUBLIC_API_BASE_URL}
ENV NODE_ENV=development
COPY package.json pnpm-lock.yaml .npmrc ./
RUN pnpm install

# Development image
FROM deps AS dev
ENV NODE_ENV=development

COPY . .
EXPOSE 3000
CMD ["pnpm", "dev"]

# Build image (produces .output)
FROM deps AS build
ENV NODE_ENV=development
COPY . .
RUN pnpm build

# Production runtime (only .output)
FROM node:22-alpine AS prod
ENV NODE_ENV=production
WORKDIR /app
COPY --from=build /app/.output ./.output
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
