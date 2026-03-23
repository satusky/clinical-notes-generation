"""HTML/CSS/JS template for the case viewer."""

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Case {case_id}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #1a1a1a;
  background: #f5f5f5;
  padding: 2rem 1rem;
}}
.container {{ max-width: 900px; margin: 0 auto; }}

/* Header */
.case-header {{
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}}
.case-header h1 {{
  font-size: 1.4rem;
  margin-bottom: 0.25rem;
}}
.case-header .subtitle {{
  color: #555;
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
}}
.badges {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }}
.badge {{
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}}
.badge-easy {{ background: #d4edda; color: #155724; }}
.badge-medium {{ background: #fff3cd; color: #856404; }}
.badge-hard {{ background: #f8d7da; color: #721c24; }}
.badge-acute {{ background: #cce5ff; color: #004085; }}
.badge-chronic {{ background: #e2d5f1; color: #4a235a; }}
.badge-resolved {{ background: #d4edda; color: #155724; }}
.badge-improving {{ background: #d1ecf1; color: #0c5460; }}
.badge-worsening {{ background: #f8d7da; color: #721c24; }}
.badge-undiagnosed {{ background: #ffeeba; color: #856404; }}
.meta-line {{
  font-size: 0.85rem;
  color: #666;
  margin-top: 0.25rem;
}}

/* Collapsible sections */
details {{
  background: #fff;
  border-radius: 8px;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}}
details > summary {{
  padding: 0.75rem 1.25rem;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  background: #fafafa;
  border-bottom: 1px solid #eee;
  list-style: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}}
details > summary::before {{
  content: "\\25B6";
  font-size: 0.7rem;
  transition: transform 0.15s;
}}
details[open] > summary::before {{
  transform: rotate(90deg);
}}
details > summary::-webkit-details-marker {{ display: none; }}
details .section-body {{ padding: 1rem 1.25rem; }}

.preview-text {{
  font-size: 0.85rem;
  color: #888;
  font-weight: normal;
  margin-left: 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 500px;
}}
details[open] .preview-text {{ display: none; }}

/* Tab bar */
.tab-bar {{
  display: flex;
  gap: 0;
  margin-bottom: 0;
  background: #fff;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}}
.tab-bar button {{
  padding: 0.6rem 1.2rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  color: #666;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  transition: color 0.15s, border-color 0.15s;
}}
.tab-bar button:hover {{ color: #333; }}
.tab-bar button.active {{
  color: #0066cc;
  border-bottom-color: #0066cc;
  font-weight: 600;
}}

/* Visit panels */
.visit-panels {{
  background: #fff;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
}}
.visit-panel {{
  display: none;
  padding: 1.25rem;
}}
.visit-panel.active {{ display: block; }}
.visit-panel h3 {{
  font-size: 1.1rem;
  margin-bottom: 0.25rem;
}}
.visit-panel .visit-meta {{
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 1rem;
}}

/* Clinical note */
.clinical-note {{
  white-space: pre-wrap;
  font-size: 0.9rem;
  line-height: 1.7;
  background: #fafafa;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #eee;
  margin-bottom: 1rem;
}}

/* Visit sub-sections */
.visit-panel details {{
  box-shadow: none;
  border: 1px solid #eee;
  margin-bottom: 0.75rem;
}}
.visit-panel details > summary {{
  background: #f9f9f9;
  font-size: 0.9rem;
  padding: 0.5rem 1rem;
}}

/* Tables */
.vitals-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}}
.vitals-table td {{
  padding: 0.3rem 0.75rem;
  border-bottom: 1px solid #f0f0f0;
}}
.vitals-table td:first-child {{
  font-weight: 600;
  width: 40%;
  color: #555;
}}

/* Lists */
.item-list {{
  list-style: disc;
  padding-left: 1.5rem;
  font-size: 0.9rem;
}}
.item-list li {{ margin-bottom: 0.25rem; }}
.pill-list {{ display: flex; flex-wrap: wrap; gap: 0.4rem; }}
.pill {{
  display: inline-block;
  background: #e8f0fe;
  color: #1a3e72;
  padding: 0.15rem 0.6rem;
  border-radius: 10px;
  font-size: 0.8rem;
}}

/* Summary list in final history */
.summary-list {{
  list-style: none;
  padding: 0;
}}
.summary-list li {{
  padding: 0.75rem 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 0.9rem;
  line-height: 1.5;
}}
.summary-list li:last-child {{ border-bottom: none; }}

.na {{ color: #aaa; font-style: italic; }}

/* Keyboard hint */
.keyboard-hint {{
  text-align: center;
  font-size: 0.75rem;
  color: #aaa;
  margin-top: -0.5rem;
  margin-bottom: 1rem;
}}
</style>
</head>
<body>
<div class="container">
{header}
{narrative}
{visit_tabs}
{visit_panels}
{final_history}
</div>
<script>
(function() {{
  var tabs = document.querySelectorAll('.tab-bar button');
  var panels = document.querySelectorAll('.visit-panel');
  var active = 0;
  function show(i) {{
    if (i < 0 || i >= tabs.length) return;
    tabs[active].classList.remove('active');
    panels[active].classList.remove('active');
    active = i;
    tabs[active].classList.add('active');
    panels[active].classList.add('active');
    tabs[active].scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'nearest' }});
  }}
  tabs.forEach(function(tab, i) {{
    tab.addEventListener('click', function() {{ show(i); }});
  }});
  document.addEventListener('keydown', function(e) {{
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'ArrowRight') show(active + 1);
    else if (e.key === 'ArrowLeft') show(active - 1);
  }});
}})();
</script>
</body>
</html>
"""
