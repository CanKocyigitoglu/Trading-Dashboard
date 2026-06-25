import {
  Box,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  OutlinedInput,
  Select,
  type SelectChangeEvent,
} from '@mui/material';

import { useFilterOptions } from '../../api/hooks';
import type { Filters } from '../../api/types';

interface MultiSelectProps {
  label: string;
  options: string[];
  value: string[];
  onChange: (value: string[]) => void;
}

function MultiSelect({ label, options, value, onChange }: MultiSelectProps) {
  const handleChange = (event: SelectChangeEvent<string[]>): void => {
    const next = event.target.value;
    onChange(typeof next === 'string' ? next.split(',') : next);
  };

  return (
    <FormControl size="small" sx={{ minWidth: 200 }}>
      <InputLabel>{label}</InputLabel>
      <Select
        multiple
        value={value}
        onChange={handleChange}
        input={<OutlinedInput label={label} />}
        renderValue={(selected) => (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {selected.map((item) => (
              <Chip key={item} label={item} size="small" />
            ))}
          </Box>
        )}
      >
        {options.map((option) => (
          <MenuItem key={option} value={option}>
            {option}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

interface FiltersBarProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

export function FiltersBar({ filters, onChange }: FiltersBarProps) {
  const { data } = useFilterOptions();

  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
      <MultiSelect
        label="Desk"
        options={data?.desks ?? []}
        value={filters.desks}
        onChange={(desks) => onChange({ ...filters, desks })}
      />
      <MultiSelect
        label="Trader"
        options={data?.traders ?? []}
        value={filters.traders}
        onChange={(traders) => onChange({ ...filters, traders })}
      />
      <MultiSelect
        label="Commodity"
        options={data?.commodities ?? []}
        value={filters.commodities}
        onChange={(commodities) => onChange({ ...filters, commodities })}
      />
    </Box>
  );
}
