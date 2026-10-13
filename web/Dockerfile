FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
# Install from the lockfile and run esbuild only after npm has finished writing
# the binary. This avoids ETXTBSY on Docker's overlay filesystem.
RUN npm ci --ignore-scripts --no-audit --no-fund \
    && node node_modules/esbuild/install.js
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

