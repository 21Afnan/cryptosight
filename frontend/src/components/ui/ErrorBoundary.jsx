import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded';
import HomeRoundedIcon from '@mui/icons-material/HomeRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("CryptoSight UI ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '80vh',
            p: 3,
          }}
        >
          <Card sx={{ maxWidth: 500, width: '100%', textAlign: 'center', p: 2, borderRadius: '24px' }}>
            <CardContent sx={{ p: '32px !important' }}>
              <Box
                sx={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: 'rgba(244, 63, 94, 0.15)',
                  color: '#F43F5E',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <ErrorOutlineRoundedIcon sx={{ fontSize: 36 }} />
              </Box>

              <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                Something went wrong
              </Typography>

              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
                {this.state.error?.message || 'An unexpected error occurred while rendering this component.'}
              </Typography>

              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1.5 }}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshRoundedIcon />}
                  onClick={() => this.setState({ hasError: false, error: null })}
                >
                  Try Again
                </Button>
                <Button
                  variant="contained"
                  startIcon={<HomeRoundedIcon />}
                  onClick={() => {
                    this.setState({ hasError: false, error: null });
                    window.location.href = '/';
                  }}
                >
                  Back to Dashboard
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>
      );
    }

    return this.props.children;
  }
}
