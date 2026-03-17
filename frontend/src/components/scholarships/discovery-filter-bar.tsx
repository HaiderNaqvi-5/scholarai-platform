"use client";

import { motion } from "framer-motion";
import { Search, ChevronDown, RotateCcw } from "lucide-react";

type FilterOption = { label: string; value: string };

type DiscoveryFilterBarProps = {
  searchQuery: string;
  onSearchChange: (val: string) => void;
  filters: {
    country: string;
    field: string;
    funding: string;
    sort: string;
  };
  onFilterChange: (key: string, val: string) => void;
  onClear: () => void;
  resultsCount: number;
};

export function DiscoveryFilterBar({
  searchQuery,
  onSearchChange,
  filters,
  onFilterChange,
  onClear,
  resultsCount
}: DiscoveryFilterBarProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-surface p-2 mb-8 flex flex-col lg:flex-row items-center gap-2 rounded-2xl"
    >
      <div className="relative flex-1 group w-full">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-400 group-focus-within:text-cobalt-600 transition-colors" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search global repository..."
          className="w-full bg-white/5 border-none outline-none pl-12 pr-4 py-3 text-sm text-neutral-900 placeholder:text-neutral-500 rounded-xl transition-all hover:bg-white/10"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
        <FilterSelect 
          value={filters.country} 
          options={[
            { label: "All Countries", value: "all" },
            { label: "USA", value: "US" },
            { label: "Canada", value: "CA" },
            { label: "UK", value: "GB" }
          ]} 
          onChange={(v) => onFilterChange("country", v)}
        />
        <FilterSelect 
          value={filters.field} 
          options={[
            { label: "All Fields", value: "all" },
            { label: "Data Science", value: "data science" },
            { label: "AI", value: "artificial intelligence" },
            { label: "Medicine", value: "medicine" }
          ]} 
          onChange={(v) => onFilterChange("field", v)}
        />
        <FilterSelect 
          value={filters.funding} 
          options={[
            { label: "Any Type", value: "all" },
            { label: "Tuition", value: "tuition_award" },
            { label: "Stipend", value: "stipend" },
            { label: "Comprehensive", value: "comprehensive_award" }
          ]} 
          onChange={(v) => onFilterChange("funding", v)}
        />
        
        <div className="h-6 w-[1px] bg-white/10 mx-2 hidden lg:block" />

        <button 
          onClick={onClear}
          className="p-3 text-neutral-400 hover:text-coral-600 hover:bg-coral-600/10 rounded-xl transition-all"
          title="Clear Filters"
        >
          <RotateCcw size={18} />
        </button>

        <div className="px-4 py-2 bg-neutral-900 text-white text-xs font-bold rounded-xl whitespace-nowrap">
          {resultsCount} Records
        </div>
      </div>
    </motion.div>
  );
}

function FilterSelect({ value, options, onChange }: { 
  value: string; 
  options: FilterOption[]; 
  onChange: (v: string) => void 
}) {

  return (
    <div className="relative group flex-1 lg:flex-none min-w-[140px]">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none w-full bg-white/5 border border-white/5 hover:bg-white/10 text-sm font-medium text-neutral-700 py-3 pl-4 pr-10 rounded-xl outline-none focus:ring-2 focus:ring-cobalt-600/20 transition-all cursor-pointer"
      >
        {options.map(o => (
          <option key={o.value} value={o.value} className="bg-white text-neutral-900">{o.label}</option>
        ))}
      </select>
      <ChevronDown size={14} className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none group-hover:text-neutral-900 transition-colors" />
    </div>
  );
}
