# Vegan Protein per Euro (for Finnish products)

A visual guide to the best-value plant-based protein sources: comparing protein density against cost across categories like legumes, soy foods, nuts, and more.

🔗 **[View the chart →](https://smallperalta.github.io/vegan-protein-economics/)**

---

## How to read the chart

- **X axis** — grams of protein per 100g of product (higher = more protein-dense)
- **Y axis** — euros per 100g of protein (lower = cheaper protein)
- **Bottom-right quadrant** (green zone) — high protein density *and* low cost: the best value zone
- Click category names in the legend to show or hide them

---

## Project structure

```
vegan-protein-economics/
├── data/
│   └── protein_foods.csv   # The product database
├── docs/
│   └── index.html          # Generated chart (served by GitHub Pages)
├── generate_chart.py       # Python script that builds the chart from the CSV
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Adding a product

Open `data/protein_foods.csv` and add a row following this format:

```
Product;Category;Package size (g);Protein in package (g);Price per kg (€);Protein per 100g;Price per 100g of protein
```

**Categories in use:** Legumes, Muesli & granola, Soy foods, Plant meat, Nuts & seeds, Textured soy protein, Plant dairy, Grain products, Protein supplement

> Tip: *Price per 100g of protein* = `(Price per kg / 10) / (Protein per 100g / 100)` — or just let the script recalculate it if you add that feature.

---

## Regenerating the chart

```bash
pip install -r requirements.txt
python generate_chart.py
```

This overwrites `docs/index.html`. Commit and push to update the live site.

---

## Deployment

The chart is hosted via **GitHub Pages** from the `docs/` folder. No server needed — the interactivity (category toggles, hover tooltips, zoom) is handled by Plotly inside the HTML file.

To enable GitHub Pages on a fork: go to *Settings → Pages → Source → Deploy from branch → `main` / `docs`*.

---

## TODO

- [ ] Add `URL` column to CSV linking to each product's store page
- [ ] Add `Store` and `Country` columns to support multi-market data
- [ ] Show product links in hover tooltips
- [ ] Consider migrating to **Streamlit** for richer interactivity (search, filters, dynamic sorting)
- [ ] Add category-level average markers to the chart
- [ ] Contributor guide for community submissions
- [ ] Consider other macros (maybe mainly FAT)
- [ ] Consider the language being in English

---

## Contributing

Data contributions are welcome. Open an issue or a pull request.

---

## License

Data is freely available. Chart code is MIT licensed.
