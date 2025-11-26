# AURORA_LIFE Frontend

Next.js 14 frontend for AURORA_LIFE platform.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Charts**: Recharts
- **HTTP**: Axios

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000)

## Features

- 📊 Dashboard with life metrics
- 📅 Event timeline
- 🤖 AI insights and predictions
- 📈 Data visualization
- 🔐 Authentication (JWT)
- 🌙 Dark mode
- 📱 Responsive design
- ⚡ Real-time updates (WebSocket)

## Project Structure

```
frontend/
├── app/              # Next.js app router pages
├── components/       # React components
├── lib/             # Utilities and API client
├── hooks/           # Custom React hooks
├── store/           # Zustand stores
├── types/           # TypeScript types
└── public/          # Static assets
```

## Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## License

MIT
