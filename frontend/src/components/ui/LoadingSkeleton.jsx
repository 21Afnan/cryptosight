import React from 'react';
import Box from '@mui/material/Box';
import Skeleton from '@mui/material/Skeleton';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';

/**
 * LoadingSkeleton — layout-aware loading skeletons.
 * Pass variant to match the content type being loaded.
 */
export function TableSkeleton({ rows = 8, columns = 6 }) {
  return (
    <Box sx={{ width: '100%' }}>
      {/* Table header */}
      <Box sx={{ display: 'flex', gap: 2, px: 2, py: 1.5, mb: 0.5 }}>
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} variant="text" width={`${100 / columns}%`} height={14} />
        ))}
      </Box>
      {/* Table rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <Box
          key={rowIdx}
          sx={{
            display: 'flex',
            gap: 2,
            px: 2,
            py: 1.25,
            borderBottom: '1px solid rgba(128,128,128,0.08)',
          }}
        >
          {Array.from({ length: columns }).map((_, colIdx) => (
            <Skeleton
              key={colIdx}
              variant="text"
              width={`${100 / columns}%`}
              height={20}
              sx={{ opacity: 1 - rowIdx * 0.08 }}
            />
          ))}
        </Box>
      ))}
    </Box>
  );
}

export function StatCardsSkeleton({ count = 5 }) {
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 2 }}>
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} sx={{ minHeight: 120 }}>
          <CardContent sx={{ p: '20px !important' }}>
            <Skeleton variant="text" width="60%" height={14} sx={{ mb: 1 }} />
            <Skeleton variant="text" width="45%" height={36} sx={{ mb: 0.5 }} />
            <Skeleton variant="text" width="30%" height={12} />
          </CardContent>
        </Card>
      ))}
    </Box>
  );
}

export function ChartSkeleton({ height = 300 }) {
  return (
    <Skeleton
      variant="rectangular"
      width="100%"
      height={height}
      sx={{ borderRadius: '16px' }}
    />
  );
}

export function DetailPageSkeleton() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Skeleton variant="text" width="35%" height={32} />
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 2 }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} variant="rectangular" height={100} sx={{ borderRadius: '20px' }} />
        ))}
      </Box>
      <Skeleton variant="rectangular" height={300} sx={{ borderRadius: '20px' }} />
      <Skeleton variant="rectangular" height={200} sx={{ borderRadius: '20px' }} />
    </Box>
  );
}

// Default export for simple use
export default function LoadingSkeleton({ variant = 'table', ...props }) {
  if (variant === 'stats') return <StatCardsSkeleton {...props} />;
  if (variant === 'chart') return <ChartSkeleton {...props} />;
  if (variant === 'detail') return <DetailPageSkeleton {...props} />;
  return <TableSkeleton {...props} />;
}
