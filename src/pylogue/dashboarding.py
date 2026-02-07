import pandas as pd
import altair as alt
from pylogue.embeds import store_html
import html as html_lib
from loguru import logger

def render_altair_chart_py(sql_query_runner: callable, sql_query: str, altair_python: str):
    """Render an Altair chart using Python code that defines `chart`.

    Always provided tooltips for interactivity in the chart.

    The code runs with access to: df (pandas DataFrame), alt (Altair), pd (
    df (pandas DataFrame), alt (Altair), pd (pandas).
    """

    try:
        local_scope = {"alt": alt, "pd": pd}
        if sql_query_runner is not None and sql_query is not None:
            df = pd.DataFrame(sql_query_runner(sql_query))
            local_scope["df"] = df
        try:
            exec(altair_python, local_scope)
        except Exception as exc:  # noqa: BLE001
            return f"Error executing Altair code: {exc}"

        chart = local_scope.get("chart")
        if chart is None or not hasattr(chart, "to_html"):
            return "Error: Altair code must define a `chart` variable."

        try:
            spec = chart.to_dict()
            html_content = chart.to_html(embed_options={"actions": False})
        except Exception as exc:  # noqa: BLE001
            return f"Error serializing chart HTML: {exc}"

        logger.debug(
            "[ALTDBG] chart class={} top-level keys={}",
            chart.__class__.__name__,
            sorted(spec.keys()),
        )
        logger.debug(
            "[ALTDBG] spec layout signals: width={!r} height={!r} vconcat={} hconcat={} concat={} layer={} facet={} repeat={}",
            spec.get("width"),
            spec.get("height"),
            "vconcat" in spec,
            "hconcat" in spec,
            "concat" in spec,
            "layer" in spec,
            "facet" in spec,
            "repeat" in spec,
        )

        width = spec.get("width")
        height = spec.get("height")
        view_cfg = (spec.get("config") or {}).get("view") or {}
        logger.debug(
            "[ALTDBG] config.view: continuousWidth={!r} continuousHeight={!r} discreteWidth={!r} discreteHeight={!r}",
            view_cfg.get("continuousWidth"),
            view_cfg.get("continuousHeight"),
            view_cfg.get("discreteWidth"),
            view_cfg.get("discreteHeight"),
        )

        if not isinstance(width, (int, float)):
            width = view_cfg.get("continuousWidth")
        if not isinstance(height, (int, float)):
            height = view_cfg.get("continuousHeight")

        if not isinstance(width, (int, float)):
            width = 300
        if not isinstance(height, (int, float)):
            height = 300
        logger.debug("[ALTDBG] resolved iframe seed size: width={} height={}", width, height)

        # Altair emits `#vis.vega-embed { width: 100% }`; override that so
        # intrinsic concat sizes can be measured from the rendered chart.
        sizing_css = (
            "<style>"
            "html,body{margin:0;padding:0;background:#fff;overflow:hidden!important;}"
            "#vis.vega-embed,.vega-embed{width:max-content!important;max-width:none!important;"
            "display:inline-flex!important;align-items:flex-start!important;justify-content:flex-start!important;}"
            "</style>"
        )
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", sizing_css + "</head>")
        else:
            html_content = sizing_css + html_content

        # Resize the iframe after Vega-Embed has actually rendered.
        # This avoids guessing padding and works for concat/facet charts.
        resize_script = (
            "<script>"
            "(function(){"
            "function setFrameSize(){"
            "if(!window.frameElement) return false;"
            "var root=document.querySelector('#vis.vega-embed')||document.querySelector('.vega-embed')||document.body;"
            "if(!root) return false;"
            "var rect=root.getBoundingClientRect();"
            "var w=Math.ceil(Math.max(rect.width||0, root.scrollWidth||0))+2;"
            "var h=Math.ceil(Math.max(rect.height||0, root.scrollHeight||0))+2;"
            "if(w>0){window.frameElement.width=String(w);window.frameElement.style.width=w+'px';}"
            "if(h>0){window.frameElement.height=String(h);window.frameElement.style.height=h+'px';}"
            "return w>0&&h>0;"
            "}"
            "var i=0,max=180;"
            "(function loop(){i++;setFrameSize();if(i<max) requestAnimationFrame(loop);})();"
            "window.addEventListener('load', function(){setTimeout(setFrameSize, 0);setTimeout(setFrameSize, 120);setTimeout(setFrameSize, 400);});"
            "})();"
            "</script>"
        )
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", resize_script + "</body>")
        else:
            html_content = html_content + resize_script

        logger.debug(
            "[ALTDBG] html stats: raw_len={} contains_vega_embed={} contains_width_100_pct={}",
            len(html_content),
            "vega-embed" in html_content,
            "width: 100%" in html_content or "width:100%" in html_content,
        )

        escaped_srcdoc = html_lib.escape(html_content, quote=True)
        iframe_html = (
            f'<iframe srcdoc="{escaped_srcdoc}" '
            f'width="{int(width)}" height="{int(height)}" '
            f'style="width:{int(width)}px; height:{int(height)}px; border:0; display:block;" '
            f'title="Altair Chart"></iframe>'
        )
        logger.debug(
            "[ALTDBG] iframe html length={} attrs width={} height={}",
            len(iframe_html),
            int(width),
            int(height),
        )

        html_id = store_html(iframe_html)
        logger.debug("[ALTDBG] stored html token={}", html_id)
        return {"_pylogue_html_id": html_id, "message": "Chart rendered."}
    except Exception as e:
        logger.debug(f"Error in render_altair_chart_py: {e}")
        return f"Error in render_altair_chart_py: {e}"
