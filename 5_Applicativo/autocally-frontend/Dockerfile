FROM node:18

# Set the working directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install
RUN npm install -D @types/node

# Copy the application code
COPY . .

# Create directory for certificates
RUN mkdir -p /app/certs

# Build the application
RUN npm run build

# Expose the development server port
EXPOSE 5173

# Start the development server with HTTPS
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# No need to expose port or run preview since Nginx will serve the files 