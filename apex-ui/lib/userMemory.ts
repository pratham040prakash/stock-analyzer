type Memory = {
  lastReviewedStock?: string;
  pastDecisions: { symbol: string; action: string }[];
};

let memory: Memory = {
  pastDecisions: [],
};

export function getMemory() {
  return memory;
}

export function updateMemory(newData: Partial<Memory>) {
  memory = { ...memory, ...newData };
}
