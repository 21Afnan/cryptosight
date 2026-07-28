import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import { useTheme } from '@mui/material/styles';

import PageContainer from '../../components/layout/PageContainer';
import StatCard from '../../components/ui/StatCard';
import StatusChip from '../../components/ui/StatusChip';
import AllocationDonut from '../../components/charts/AllocationDonut';
import EquityCurveChart from '../../components/charts/EquityCurveChart';
import LoadingSkeleton from '../../components/ui/LoadingSkeleton';
import EmptyState from '../../components/ui/EmptyState';
import { useMockFetch } from '../../hooks/useMockFetch';
import { getWallets } from '../../api/walletsApi';
import { COLORS } from '../../theme/theme';

import AccountBalanceWalletRoundedIcon from '@mui/icons-material/AccountBalanceWalletRounded';
import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded';
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';
import RocketLaunchRoundedIcon from '@mui/icons-material/RocketLaunchRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';

export default function AccountOverview() {
  const theme = useTheme();
  const navigate = useNavigate();
  const isDark = theme.palette.mode === 'dark';

  const { data: walletsRes, loading, error } = useMockFetch(getWallets);
  const wallets = walletsRes?.data ?? [];

  // Calculate account summary KPIs
  const kpis = useMemo(() => {
    const totalBalance = wallets.reduce((acc, w) => acc + (w.balance || 0), 0);
    const connectedCount = wallets.filter((w) => w.status === 'connected').length;
    const totalUnrealizedPnL = wallets.reduce((acc, w) => acc + (w.unrealized_pnl || 0), 0);
    const totalRealizedPnL = wallets.reduce((acc, w) => acc + (w.total_pnl || 0), 0);
    const runningExecutionsCount = wallets.reduce((acc, w) => acc + (w.running_executions?.length || 0), 0);

    return [
      {
        title: 'Total Account Balance',
        value: `$${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
        delta: `across ${wallets.length} exchange accounts`,
        deltaType: 'neutral',
        icon: <AccountBalanceWalletRoundedIcon />,
        colorIndex: 0,
      },
      {
        title: 'Connected Exchanges',
        value: `${connectedCount} / ${wallets.length}`,
        delta: 'Active API sessions',
        deltaType: 'positive',
        icon: <CheckCircleRoundedIcon />,
        colorIndex: 1,
      },
      {
        title: 'Unrealized PnL',
        value: `${totalUnrealizedPnL >= 0 ? '+' : ''}$${totalUnrealizedPnL.toFixed(2)}`,
        delta: 'Open active positions',
        deltaType: totalUnrealizedPnL >= 0 ? 'positive' : 'negative',
        icon: <ShowChartRoundedIcon />,
        colorIndex: 2,
      },
      {
        title: 'Total Realized PnL',
        value: `${totalRealizedPnL >= 0 ? '+' : ''}$${totalRealizedPnL.toFixed(2)}`,
        delta: 'Cumulative net profit',
        deltaType: totalRealizedPnL >= 0 ? 'positive' : 'negative',
        icon: <AccountBalanceWalletRoundedIcon />,
        colorIndex: 3,
      },
      {
        title: 'Live Executions',
        value: runningExecutionsCount,
        delta: 'Active strategy bots',
        deltaType: 'neutral',
        icon: <RocketLaunchRoundedIcon />,
        colorIndex: 4,
      },
    ];
  }, [wallets]);

  // Donut chart data for account balance distribution
  const allocationData = useMemo(() => {
    return wallets.map((w) => ({
      name: `${w.exchange} (${w.account_type})`,
      value: w.balance || 0,
    }));
  }, [wallets]);

  // Sample equity curve data for account growth
  const equityCurveData = useMemo(() => {
    const points = [];
    let val = 60000;
    let d = new Date('2025-01-01');
    for (let i = 0; i < 90; i++) {
      val += (Math.random() - 0.44) * 500;
      points.push({
        time: d.toISOString().split('T')[0],
        value: parseFloat(val.toFixed(2)),
      });
      d.setDate(d.getDate() + 1);
    }
    return points;
  }, []);

  if (loading) {
    return (
      <PageContainer title="Account Overview">
        <Box sx={{ pt: 3 }}><LoadingSkeleton variant="detail" /></Box>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer title="Account Overview">
        <EmptyState icon={ErrorOutlineRoundedIcon} title="Failed to load accounts" description={error} />
      </PageContainer>
    );
  }

  return (
    <PageContainer title="Account Overview">
      <Box sx={{ pt: 2 }}>
        {/* Equal-sized StatCards Grid with soft 3D hover effects */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(3, 1fr)',
              lg: 'repeat(5, 1fr)',
            },
            gap: 2,
            mb: 3,
          }}
        >
          {kpis.map((kpi, idx) => (
            <StatCard key={kpi.title} {...kpi} colorIndex={idx} />
          ))}
        </Box>

        {/* Charts Row: Account Equity Curve (8 cols) + Account Allocation Donut (4 cols) */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} lg={8}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: '20px !important' }}>
                <Typography variant="h5" sx={{ mb: 0.5, fontWeight: 700 }}>
                  Combined Account Equity Curve
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                  Cumulative portfolio balance across all exchange wallets (90 days)
                </Typography>
                <Box sx={{ height: 280 }}>
                  <EquityCurveChart data={equityCurveData} height={280} label="Total Balance" />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: '20px !important' }}>
                <Typography variant="h5" sx={{ mb: 0.5, fontWeight: 700 }}>
                  Account Allocation
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                  Capital distribution per exchange
                </Typography>
                <AllocationDonut
                  data={allocationData}
                  centerLabel="Total Balance"
                  centerValue={`$${kpis[0].value.replace('$','')}`}
                  size={220}
                  showLegend
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Detailed Account List with Running Strategies */}
        <Card>
          <CardContent sx={{ p: '20px !important' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" sx={{ fontWeight: 700 }}>
                Accounts & Active Running Strategies
              </Typography>
              <Button variant="outlined" size="small" onClick={() => navigate('/wallets')}>
                Manage Wallets
              </Button>
            </Box>

            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Exchange & Account</TableCell>
                    <TableCell>API Key</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Balance</TableCell>
                    <TableCell align="right">Unrealized PnL</TableCell>
                    <TableCell align="right">Total Realized PnL</TableCell>
                    <TableCell>Active Running Strategies</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {wallets.map((w) => (
                    <TableRow key={w.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 700 }}>
                            {w.exchange}
                          </Typography>
                          <Chip label={w.account_type} size="small" sx={{ fontSize: 11 }} />
                        </Box>
                      </TableCell>

                      <TableCell>
                        <Typography variant="body2" sx={{ fontSize: 12, color: theme.palette.text.secondary }}>
                          {w.api_key}
                        </Typography>
                      </TableCell>

                      <TableCell>
                        <StatusChip status={w.status} />
                      </TableCell>

                      <TableCell align="right">
                        <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
                          ${w.balance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </Typography>
                      </TableCell>

                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          sx={{
                            color: w.unrealized_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed,
                            fontWeight: 700,
                            fontVariantNumeric: 'tabular-nums',
                          }}
                        >
                          {w.unrealized_pnl >= 0 ? '+' : ''}${w.unrealized_pnl?.toFixed(2)}
                        </Typography>
                      </TableCell>

                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          sx={{
                            color: w.total_pnl >= 0 ? COLORS.pnlGreen : COLORS.pnlRed,
                            fontWeight: 700,
                            fontVariantNumeric: 'tabular-nums',
                          }}
                        >
                          {w.total_pnl >= 0 ? '+' : ''}${w.total_pnl?.toFixed(2)}
                        </Typography>
                      </TableCell>

                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
                          {w.assigned_strategies?.length === 0 ? (
                            <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                              None running
                            </Typography>
                          ) : (
                            w.assigned_strategies?.map((s) => (
                              <Chip
                                key={s.strategy_id}
                                label={`${s.strategy_name} (${s.symbol})`}
                                size="small"
                                onClick={() => navigate(`/strategies/${s.strategy_id}`)}
                                sx={{
                                  fontSize: 11,
                                  fontWeight: 600,
                                  color: COLORS.accent,
                                  background: `${COLORS.accent}15`,
                                  cursor: 'pointer',
                                  '&:hover': { background: `${COLORS.accent}30` },
                                }}
                              />
                            ))
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>
    </PageContainer>
  );
}
