# --- Build stage -----------------------------------------------------------
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# The API base URL the browser should call. Override at build time:
#   docker compose build --build-arg VITE_API_URL=https://api.example.com/api
ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=$VITE_API_URL NITRO_PRESET=node-server

RUN npm run build

# --- Runtime stage ---------------------------------------------------------
# Do NOT pin NITRO_PORT: the server listens on $PORT (Render) and falls back
# to 3000 locally. Nitro precedence: NITRO_PORT ?? PORT ?? 3000.
FROM node:22-alpine AS runtime
WORKDIR /app
ENV NITRO_HOST=0.0.0.0
COPY --from=build /app/.output ./.output
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]