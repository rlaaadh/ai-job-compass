import CircularProgress from "@mui/material/CircularProgress";

export default function Spinner({ size = 32 }: { size?: number }) {
  return <CircularProgress size={size} />;
}
