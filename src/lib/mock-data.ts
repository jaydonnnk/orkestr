export type Persona = "alice" | "bob" | "carol" | "dave" | "eve";

export interface Friend {
  id: Persona;
  name: string;
  initials: string;
}

export const FRIENDS: Friend[] = [
  { id: "alice", name: "Alice", initials: "A" },
  { id: "bob", name: "Bob", initials: "B" },
  { id: "carol", name: "Carol", initials: "C" },
  { id: "dave", name: "Dave", initials: "D" },
  { id: "eve", name: "Eve", initials: "E" },
];

export const SPLITS = [
  {
    id: "dinner-trattoria",
    title: "Dinner at Trattoria",
    ref: "SPL-2847",
    total: 156.0,
    yourShare: 31.2,
    status: "active" as const,
    date: "Sat 14 Jun",
    paidBy: "alice" as Persona,
  },
  {
    id: "weekend-cabin",
    title: "Weekend cabin",
    ref: "SPL-2812",
    total: 420.0,
    yourShare: 84.0,
    status: "pending" as const,
    date: "Fri 7 Jun",
    paidBy: "bob" as Persona,
  },
  {
    id: "groceries-run",
    title: "Groceries run",
    ref: "SPL-2799",
    total: 68.5,
    yourShare: 13.7,
    status: "settled" as const,
    date: "Mon 3 Jun",
    paidBy: "carol" as Persona,
  },
];

export const SHOWCASE_SCREENS = [
  { href: "/buttons", title: "Buttons", description: "Primary, secondary, tertiary, destructive & icon" },
  { href: "/cards", title: "Cards", description: "Default, surface & dark settled cards" },
  { href: "/inputs", title: "Text inputs", description: "Create a new split form" },
  { href: "/badges", title: "Badges & pills", description: "Amber, negative, ref & status" },
  { href: "/navigation", title: "Navigation tabs", description: "Active splits, owed & settled" },
  { href: "/avatars", title: "Avatars", description: "Friend persona colours & sizes" },
  { href: "/typography", title: "Typography & amounts", description: "Display, body & tabular figures" },
  { href: "/split-detail", title: "Split detail", description: "Composite screen — dinner split" },
  { href: "/settled", title: "Settled passport", description: "Dark card final state" },
];
