// File: SearchableDropdown.tsx. Description: Reusable searchable dropdown with case-insensitive starts-with filtering.
"use client";

import { useState, useEffect, useRef } from "react";
import { ChevronDown } from "lucide-react";

interface SearchableDropdownProps {
  id: string;
  placeholder: string;
  options: string[];
  value: string;
  onChange: (val: string) => void;
  disabled?: boolean;
}

export function SearchableDropdown({
  id,
  placeholder,
  options,
  value,
  onChange,
  disabled = false,
}: SearchableDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle clicking outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter options based on input value starting with input prefix (case-insensitive)
  // If search value is empty, display all options
  const filteredOptions = value
    ? options.filter((option) =>
        option.toLowerCase().startsWith(value.toLowerCase())
      )
    : options;

  const handleSelect = (option: string) => {
    onChange(option);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative w-full">
      <div className="relative flex items-center">
        <input
          id={id}
          className="input-field w-full pr-10"
          placeholder={placeholder}
          value={value}
          disabled={disabled}
          onChange={(e) => {
            onChange(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
        />
        <button
          type="button"
          disabled={disabled}
          onClick={() => setIsOpen(!isOpen)}
          className="absolute right-3 text-text-secondary hover:text-text-primary transition-colors disabled:opacity-50"
        >
          <ChevronDown
            size={18}
            className={`transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
          />
        </button>
      </div>

      {isOpen && !disabled && (
        <div className="absolute top-full left-0 right-0 mt-1.5 max-h-60 overflow-y-auto bg-bg-secondary/95 backdrop-blur-xl border border-border/80 rounded-xl shadow-2xl z-50 animate-in fade-in slide-in-from-top-2 duration-250 scrollbar-thin">
          {filteredOptions.length > 0 ? (
            <div className="py-1">
              {filteredOptions.map((option, idx) => (
                <button
                  key={`${option}-${idx}`}
                  type="button"
                  onClick={() => handleSelect(option)}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-app-accent/10 hover:text-app-accent transition-colors ${
                    value.toLowerCase() === option.toLowerCase()
                      ? "bg-app-accent/5 text-app-accent font-medium"
                      : "text-text-primary"
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          ) : (
            <div className="px-4 py-3 text-sm text-text-secondary italic">
              No matching options found. Press enter or leave to use typed value.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
