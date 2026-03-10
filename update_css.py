
import sys
import os

path = r'd:\sp\p-2\codes\static\css\style.css'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_styles = """/* ─── Pricing Section ────────────────────────── */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-top: 16px;
}

.pricing-card {
  padding: 40px 32px;
  background: #fff;
  border-radius: 16px;
  border: 1px solid var(--border);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
}

.pricing-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.1);
}

.pricing-card.featured {
  border: 2px solid var(--accent);
  box-shadow: 0 15px 30px -5px rgba(37, 99, 235, 0.15);
}

.plan-name {
  font-size: 0.85rem;
  font-weight: 800;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 12px;
}

.plan-price {
  font-size: 3rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 24px;
  display: flex;
  align-items: baseline;
}

.plan-price span {
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-muted);
  margin-left: 4px;
}

.plan-features {
  list-style: none;
  margin-bottom: 32px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
}

.plan-features li {
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-main);
}

.plan-features li::before {
  content: '✓';
  color: var(--green);
  font-weight: 800;
  background: rgba(16, 185, 129, 0.1);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
}

.plan-option {
  transition: all 0.2s ease;
}

.plan-option:hover {
  background: var(--bg-hover) !important;
  border-color: var(--accent) !important;
}

.plan-option.selected {
  background: var(--accent-light) !important;
  border-color: var(--accent) !important;
}
"""

start_idx = 1118
end_idx = 1180

if "Pricing Section" in lines[start_idx]:
    lines[start_idx:end_idx] = [new_styles + "\n"]
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUCCESS")
else:
    print(f"ERROR: Expected line 1119 to contain 'Pricing Section', but got: {lines[start_idx]}")
