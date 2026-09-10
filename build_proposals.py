#!/usr/bin/env python3
# Generates the corrected English and Arabic proposal docx files.
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

W = "/home/mobta/university/malik"

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def set_rtl(paragraph, on=True):
    if on:
        paragraph._p.set(qn('xml:lang'), 'ar')
        rpr = paragraph._p.get_or_add_pPr()
        rpr.set(qn('w:bidi'), 'true')

def add_heading(doc, text, level=1, rtl=False):
    p = doc.add_heading(text, level=level)
    if rtl:
        set_rtl(p)
    return p

def add_para(doc, text, rtl=False, bold=False, size=None, align=None):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    if rtl:
        set_rtl(p)
    run = p.add_run(text)
    if bold:
        run.bold = True
    if size:
        run.font.size = Pt(size)
    return p

def add_bullet(doc, text, rtl=False):
    p = doc.add_paragraph(style='List Bullet')
    if rtl:
        set_rtl(p)
    p.add_run(text)
    return p

def add_table(doc, headers, rows, rtl=False):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Light Grid Accent 1'
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ''
        r = hdr[i].paragraphs[0].add_run(h)
        r.bold = True
        if rtl:
            set_rtl(hdr[i].paragraphs[0])
    for row in rows:
        cells = t.add_row().cells
        for i, c in enumerate(row):
            cells[i].text = ''
            para = cells[i].paragraphs[0]
            if rtl:
                set_rtl(para)
            para.add_run(c)
    return t

# ============================================================================
# ENGLISH VERSION
# ============================================================================
def build_en():
    doc = Document()
    # Title block
    add_para(doc, "Evaluating Trust Boundaries in MCP Apps: An Experimental Study of Host-Mediated Capabilities",
             rtl=False, bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "Research Proposal", rtl=False, size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "Emirates International University", rtl=False, size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "Prof. Dr. Malik Nasir Ali Al-Jabri (Supervisor); Mubarak Walid Al-Hamadi; Yasin Abd Al-Aziz Al-Khalqi; Muhammad Saif Ali Al-Heimi",
             rtl=False, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "2026 / 8", rtl=False, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

    add_para(doc, "Abstract", bold=True)
    add_para(doc,
        "MCP Apps let an MCP server deliver interactive user interfaces that a host renders inside a sandbox. "
        "The sandbox isolates the UI from the host, but the UI can still request host-mediated capabilities such as opening a link, "
        "sending a chat message, or updating the model context. Protection therefore depends not only on isolation but also on the "
        "policy decisions the host applies to these requests (Salomon et al., 2026). This proposal presents a reproducible experimental "
        "study of the boundary between what isolation technically forbids and what the host must govern by policy. We compare a "
        "specification-compliant host (baseline) with the same host augmented by a small host-side policy layer (treatment), measuring "
        "security, continued legitimate functionality, and processing latency. We state three testable hypotheses and an honest "
        "proof-of-concept scope.")

    # 1
    add_heading(doc, "1. Introduction", 1)
    add_para(doc,
        "The Model Context Protocol (MCP) lets AI applications interact with external tools and resources in a uniform way. "
        "The MCP Apps extension adds interactive interfaces delivered by an MCP server and rendered by the host inside an isolated "
        "environment, instead of merely returning text and data (Hou et al., 2025; Model Context Protocol, 2026b).")
    add_para(doc,
        "The host sandbox protects the host from direct access to its page and data, but an MCP App interface can request capabilities "
        "that the host executes, such as opening a link, sending a message to the conversation, or updating the model context. "
        "Protection therefore does not stop at isolation; it also depends on the decisions and policies the host applies to these requests "
        "(Salomon et al., 2026).")
    add_para(doc,
        "The study's importance lies in focusing on the boundary between what isolation technically forbids and what the host must "
        "regulate by its policies. The study will present a practical test of this boundary, then compare a specification-compliant host "
        "with the same host after adding a specific policy layer, thereby helping reduce risk while preserving legitimate functionality.")

    # 2
    add_heading(doc, "2. Related Work", 1)
    add_para(doc,
        "MCP security studies have focused on server and tool risks, permission management, and indirect prompt injection. They show "
        "that connecting models to tools can lead to unwanted execution or data disclosure if trust and permissions are not set correctly "
        "(Hou et al., 2025; Maloyan & Namiot, 2026; Radosevich & Halloran, 2025). AgentDojo and AgentBound introduced security-testing "
        "methods and execution-boundary enforcement, but did not focus on MCP App interface messages to the host (Bühler et al., 2026; "
        "Debenedetti et al., 2024).")
    add_para(doc,
        "The MCP Apps specification and SEP-1865 define isolation, CSP, tool visibility, and host-mediated channels, but they present "
        "design requirements rather than an experimental comparison of an additional hardening layer (Model Context Protocol, 2026b; "
        "Salomon et al., 2026).")

    add_heading(doc, "2.1 Brief Comparison of Prior Work", 2)
    add_table(doc,
        ["Authors / Year", "Title", "Strengths", "Weaknesses / Gaps"],
        [
            ["Model Context Protocol; Salomon et al. (2026)", "MCP Apps Specification & SEP-1865",
             "Define the formal architecture, threat model, and controls (CSP, tool visibility, host channels).",
             "No experimental before/after comparison with an added host policy layer."],
            ["Maloyan & Namiot (2026)", "Breaking the Protocol",
             "Specification analysis; experiments on injection and trust.", "Focuses on base MCP, not the interactive App channels."],
            ["Bühler et al. (2026)", "AgentBound",
             "Enforces policies on MCP server execution.", "Addresses system level, not interface messages."],
            ["Hou et al. (2025)", "MCP: Landscape, Security Threats, and Future Research Directions",
             "Broad taxonomy of MCP risks and server lifecycle.", "Does not focus on MCP Apps interfaces and host decisions."],
            ["Radosevich & Halloran (2025)", "MCP Safety Audit",
             "Practical audit of MCP server and tool risks.", "Does not test the boundary between MCP App interface and host."],
            ["Debenedetti et al. (2024)", "AgentDojo",
             "Measures security while preserving legitimate work.", "General agent environment, not an MCP host / Apps setting."],
            ["Greshake et al. (2023)", "Not What You've Signed Up For",
             "Shows indirect prompt-injection risk.", "Not specific to MCP Apps."],
        ])

    add_heading(doc, "2.2 Research Gap", 2)
    add_para(doc,
        "Within the sources we reviewed, prior studies focused on MCP server and tool security, or on prompt injection and agent "
        "isolation. We found no focused experimental study that compares a specification-compliant MCP Apps host with the same host after "
        "enabling an additional policy to govern host-mediated capabilities, while measuring security, preservation of functionality, and "
        "performance. This work addresses that gap by building a reproducible test environment and a small policy-layer prototype.")

    # 3
    add_heading(doc, "3. Aim and Contribution", 1)
    add_heading(doc, "3.1 Research Aim", 2)
    add_para(doc,
        "To measure the protection boundary in MCP Apps in practice, identify the difference between mandatory isolation requirements and "
        "decisions that depend on host policy, then test a preliminary solution that reduces misuse of allowed channels.")
    add_heading(doc, "3.2 Expected Contribution", 2)
    add_bullet(doc, "A reproducible test suite that separates specification-compliance tests from residual-risk tests.")
    add_bullet(doc, "A host-side policy-layer prototype that governs links, messages, and model-context updates and makes the interface's origin explicit.")
    add_bullet(doc, "A before/after comparison in terms of security, continued legitimate functionality, and processing latency.")
    add_para(doc,
        "Novelty note: the individual controls (link allow-lists, explicit consent, origin display, rate/size limits, audit logging) are "
        "good practice rather than inventions. The novel element of this work is twofold: (a) the empirical quantification of residual "
        "risk that remains possible through channels the specification explicitly allows, and (b) the trust-boundary marker treated as a "
        "measurable UI affordance whose effect is evaluated rather than assumed.")

    # 4
    add_heading(doc, "4. Research Problems", 1)
    add_heading(doc, "4.1 Main Problem", 2)
    add_para(doc,
        "MCP Apps isolate the interface from the host but allow it to request operations the host executes. The literature we reviewed "
        "lacks a simple experimental evaluation showing what the specification forbids mandatorily, what may remain possible through "
        "allowed channels, and how effective an added host policy is at reducing that risk.")
    add_heading(doc, "4.2 Sub-Problems", 2)
    add_bullet(doc, "SP1: the need to verify practically that the host complies with CSP boundaries and tool/resource visibility.")
    add_bullet(doc, "SP2: the possibility of misusing allowed channels such as ui/open-link, ui/message, and ui/update-model-context without breaking the sandbox.")
    add_bullet(doc, "SP3: the need to know whether an added policy layer reduces unwanted behavior without disabling legitimate work or adding large latency.")
    add_heading(doc, "4.3 Hypotheses and Proposed Solution", 2)
    add_table(doc,
        ["Hypothesis (testable)", "Problem"],
        [
            ["H1: The specification-compliant host will reject all test cases violating CSP and tool/resource visibility, and will allow legitimate compliant cases. (SP1)",
             "SP1"],
            ["H2: The proposed policy layer will reduce the number of sensitive actions executed without approval and block transfer of the synthetic value through a non-sanctioned channel, compared with baseline. (SP2)",
             "SP2"],
            ["H3: The layer will preserve all predefined legitimate control cases, and the median added local processing overhead will not exceed 20 ms. (SP3)",
             "SP3"],
        ])
    add_para(doc,
        "Baseline behavior clarification: the specification-compliant baseline host implements the MUST-level sandbox, CSP, and "
        "tool/resource-visibility requirements, but issues no mandatory approval prompt for ui/open-link, ui/message, or "
        "ui/update-model-context. Absent the policy layer, it dispatches these requests per the specification's default handling (opens the "
        "external link, delivers the message to the chat, updates the model context). This default dispatch is precisely the residual-risk "
        "surface the policy layer targets.")
    add_para(doc,
        "Proposed solution: a layer inside the host intercepts sensitive requests before execution and applies a link allow-list, explicit "
        "consent, interface-origin display, size and rate limits, and an audit log. Hypotheses are accepted or rejected per actual results; "
        "the study does not assume the solution succeeds in advance.")

    # 5
    add_heading(doc, "5. Importance and Objectives", 1)
    add_heading(doc, "5.1 Importance of the Study", 2)
    add_para(doc,
        "The study shows the host's responsibility when handling an interface delivered by an untrusted server, and prevents confusion "
        "between sandbox protection and host-policy protection. It also offers a test and a prototype that MCP host developers can reuse.")
    add_heading(doc, "5.2 General Objective", 2)
    add_para(doc,
        "To evaluate trust boundaries in MCP Apps, build a small host-side policy layer, and measure its effect experimentally.")
    add_heading(doc, "5.3 Specific Objectives", 2)
    add_bullet(doc, "Extract the mandatory security requirements and the host-policy-dependent channels.")
    add_bullet(doc, "Build a local lab, establish a unified baseline, and define repeatable scenarios.")
    add_bullet(doc, "Implement the proposed policy layer and run the same scenarios after enabling it.")
    add_bullet(doc, "Compare security, functionality, and performance, and accept or reject the hypotheses per results.")

    # 6
    add_heading(doc, "6. Methodology", 1)
    add_heading(doc, "6.1 Study Type and Design", 2)
    add_para(doc,
        "The study uses an applied experimental method inside an isolated local lab. The same cases are executed in two groups:")
    add_bullet(doc, "Baseline: a test host implementing the MUST requirements of the MCP Apps specification, without the extra policy layer.")
    add_bullet(doc, "Treatment: the same host and environment, with only the proposed layer enabled.")
    add_para(doc,
        "The independent variable is the layer state (off/on). The dependent variables are allow/deny decisions, execution of actions "
        "without approval, access to synthetic data, success of legitimate functionality, and processing latency.")
    add_heading(doc, "6.2 Test Environment and Scope", 2)
    add_bullet(doc, "A single Linux machine in an isolated local environment.")
    add_bullet(doc, "One test host built on basic-host and AppBridge from the ext-apps project (Model Context Protocol, 2026a).")
    add_bullet(doc, "A local MCP server, a legitimate interface, and an untrusted test interface.")
    add_bullet(doc, "Dummy tools and resources, a local receiver server, and a test value such as SYNTHETIC_SECRET_001.")
    add_bullet(doc, "A unified log of JSON-RPC messages, policy decisions, and timings.")
    add_para(doc,
        "The attacker is assumed to control the MCP server and interface but has no direct access to the user's device. The study does not "
        "break the browser, escape the sandbox, or run phishing on real people.")
    add_heading(doc, "6.3 Proposed Solution", 2)
    add_para(doc, "The policy layer intercepts interface messages before execution and applies four rules:")
    add_bullet(doc, "1. Links: protocol scheme validation (http/https) and explicit user consent prior to dispatching window.open.")
    add_bullet(doc, "2. Messages and context: explicit user consent, origin source badge display, and message size caps (4 KB limit).")
    add_bullet(doc, "3. Visible trust boundary: add a persistent marker around the interface stating it is delivered by an external MCP server.")
    add_bullet(doc, "4. Audit: log source, request type, decision, reason, and processing time without storing sensitive data.")
    add_para(doc,
        "CSP and tool-visibility tests remain part of baseline specification compliance, not a new contribution of the layer. The novel, "
        "evaluated element here is the measurable trust-boundary marker and the empirical residual-risk measurement through allowed channels.")
    add_heading(doc, "6.4 Implementation Steps", 2)
    add_bullet(doc, "1. Run the official example; verify a legitimate interface displays and an allowed tool is called.")
    add_bullet(doc, "2. Build the local server, the two interfaces, dummy tools/resources, and the receiver server.")
    add_bullet(doc, "3. Install test cases; run them in Baseline and record results.")
    add_bullet(doc, "4. Implement the policy layer as a toggleable module.")
    add_bullet(doc, "5. Run the same cases in Treatment with identical settings and data.")
    add_bullet(doc, "6. Compare results and test H1-H3; write conclusions.")
    add_heading(doc, "6.5 Test Matrix", 2)
    add_table(doc,
        ["Test", "Baseline (expected)", "Treatment (expected)", "Metric"],
        [
            ["Legitimate tool with app access", "Allow", "Allow", "Function preserved"],
            ["Non-visible tool to the app", "Reject", "Reject", "Spec compliance"],
            ["Connection to a domain not declared in CSP", "Reject", "Reject", "CSP compliance"],
            ["Open external link", "No approval prompt; link opened per default spec handling (observed/logged)", "Consent then allow/deny", "Execution without approval"],
            ["ui/message or update-model-context to host", "Delivered with no origin indicator (observed/logged)", "Consent and source shown", "Channel integrity"],
            ["Host-impersonating interface", "Rendered inside isolation", "Persistent source marker shown", "Trust-boundary clarity"],
            ["Predefined legitimate operation", "Success", "Success", "False block"],
        ])
    add_para(doc,
        "We study three host-mediated capability categories: (1) link opening (ui/open-link), (2) messaging and model-context update "
        "(ui/message, ui/update-model-context), and (3) audit/observability. The exfiltration test places SYNTHETIC_SECRET_001 in a "
        "ui/message body and in a ui/update-model-context payload and checks whether it reaches the local receiver.")
    add_heading(doc, "6.6 Measurement and Analysis", 2)
    add_bullet(doc, "Number of successful compliance tests out of the total.")
    add_bullet(doc, "Number of sensitive requests executed without approval before and after the layer.")
    add_bullet(doc, "Success or failure of synthetic-value transfer per channel.")
    add_bullet(doc, "Ratio of successful legitimate operations and count of falsely blocked operations.")
    add_bullet(doc, "Audit-log completeness and mean/median processing time at the 95th percentile.")
    add_para(doc,
        "Hypothesis acceptance plan: H1 is accepted if Baseline rejects 100% of CSP-violating and tool-non-visible cases and allows 100% "
        "of legitimate compliant cases; otherwise rejected. H2 is accepted if Treatment reduces sensitive actions without approval to zero "
        "and blocks transfer of SYNTHETIC_SECRET_001 via ui/message and ui/update-model-context; otherwise rejected. H3 is accepted if all "
        "predefined legitimate control cases succeed in Treatment and the median local policy overhead is <= 20 ms; otherwise rejected.")
    add_para(doc,
        "Each functional case runs five times per group. Performance is measured 30 times after five warm-up runs that are excluded. "
        "Results are shown as counts, percentages, and milliseconds, then compared with the H1-H3 expectations. The 20 ms figure is an "
        "initial operational threshold set by the researchers for in-lab evaluation, not a normative limit in the MCP Apps specification.")
    add_heading(doc, "6.7 Ethical Controls and Limitations", 2)
    add_para(doc,
        "All experiments run locally with synthetic data and accounts, and target no public services or real users. Results are limited to "
        "one host and three capability categories; the prototype is therefore a proof of concept, not a finished security product.")

    # 7
    add_heading(doc, "7. Time Plan", 1)
    add_para(doc, "The research runs over six weeks.")
    add_table(doc,
        ["Period", "Main Work", "Output", "Direct Cost"],
        [
            ["Week 1", "Review specification; run official example; fix test plan.", "Working lab + fixed test plan", "0"],
            ["Week 2", "Build the two interfaces; run Baseline cases.", "Baseline results", "0"],
            ["Week 3", "Complete Baseline measurements; finalize Baseline logs.", "Finalized Baseline results", "0"],
            ["Week 4", "Implement the policy layer as a toggleable module.", "Policy-layer module", "0"],
            ["Week 5", "Run the same cases in Treatment.", "Post-solution results", "0"],
            ["Week 6", "Analyze results; test H1-H3; write report.", "Final report", "0"],
        ])
    add_para(doc,
        "No direct cost is expected: the machine is available, tools are open source, and experiments are local. Any contingent cost is "
        "documented in the actual report.")

    # 8
    add_heading(doc, "8. References", 1)
    refs = [
        "Bühler, C., Biagiola, M., Di Grazia, L., & Salvaneschi, G. (2026). AgentBound: Securing execution boundaries of AI agents. Proceedings of the 34th ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering. https://doi.org/10.1145/3808103",
        "Debenedetti, E., Zhang, J., Balunović, M., Beurer-Kellner, L., Fischer, M., & Tramèr, F. (2024). AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses in LLM agents. NeurIPS 2024 Datasets and Benchmarks Track. https://arxiv.org/abs/2406.13352",
        "Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection. Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security. https://arxiv.org/abs/2302.12173",
        "Hou, X., Zhao, Y., Wang, S., & Wang, H. (2025). Model Context Protocol (MCP): Landscape, security threats, and future research directions. arXiv:2503.23278. https://arxiv.org/abs/2503.23278",
        "Maloyan, N., & Namiot, D. (2026). Breaking the Protocol: Security analysis of the Model Context Protocol specification and prompt injection vulnerabilities in tool-integrated LLM agents. arXiv:2601.17549. https://arxiv.org/abs/2601.17549",
        "Model Context Protocol. (2026a). ext-apps: Specification and SDK for the MCP Apps extension [Source code]. https://github.com/modelcontextprotocol/ext-apps",
        "Model Context Protocol. (2026b). MCP Apps specification (revision 2026-01-26). https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx",
        "Radosevich, B., & Halloran, J. (2025). MCP safety audit: LLMs with the Model Context Protocol allow major security exploits. arXiv:2504.03767. https://arxiv.org/abs/2504.03767",
        "Salomon, I., Yosef, L., Chafik, O., Swannack, J., Hefner, J., Pidkuiko, A., Cooper, N., Ashley, B., & Christakis, A. (2026). SEP-1865: MCP Apps—Interactive user interfaces for MCP. Model Context Protocol. https://modelcontextprotocol.io/seps/1865-mcp-apps-interactive-user-interfaces-for-mcp",
    ]
    for r in refs:
        p = doc.add_paragraph(r)
        p.paragraph_format.left_indent = Pt(18)
        p.paragraph_format.first_line_indent = Pt(-18)

    doc.save(f"{W}/MCP_Apps_Trust_Boundaries_Proposal_EN.docx")
    print("EN saved")

# ============================================================================
# ARABIC VERSION
# ============================================================================
def build_ar():
    doc = Document()
    # default font that supports Arabic
    style = doc.styles['Normal']
    style.font.name = 'DejaVu Sans'
    style.element.rPr.rFonts.set(qn('w:eastAsia'), 'DejaVu Sans')

    add_para(doc, "تقييم حدود الثقة في MCP Apps: دراسة تجريبية للقدرات التي يديرها المضيف",
             rtl=True, bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "مقترح بحثي", rtl=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "الجامعة الإماراتية الدولية", rtl=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "أ.د. مالك ناصر علي الجبري (مشرفًا أكاديميًا)؛ مبارك وليد الحمادي؛ ياسين عبد العزيز الخالقي؛ محمد سيف علي الحيمي",
             rtl=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "2026 / 8", rtl=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

    add_para(doc, "ملخص", bold=True, rtl=True)
    add_para(doc,
        "يسمح امتداد MCP Apps لخادم MCP بتقديم واجهات تفاعلية يعرضها المضيف داخل بيئة معزولة. يحمي هذا العزل الواجهة من المضيف، لكن "
        "الواجهة تظل قادرة على طلب قدرات يديرها المضيف مثل فتح رابط أو إرسال رسالة محادثة أو تحديث سياق النموذج. لذلك لا تقتصر الحماية "
        "على العزل، بل تعتمد أيضًا على قرارات السياسات التي يطبقها المضيف على هذه الطلبات (Salomon et al., 2026). يقدم هذا المقترح دراسة "
        "تجريبية قابلة للتكرار لحدود الفصل بين ما يمنعه العزل تقنيًا وما يجب أن يضبطه المضيف بسياساته. نقارن بين مضيف ملتزم بالمواصفة "
        "(خط الأساس) وبين المضيف نفسه بعد إضافة طبقة سياسة صغيرة على جانب المضيف (المعالجة)، مع قياس الأمن واستمرار الوظائف المشروعة "
        "وزمن المعالجة. ونصوغ ثلاث فرضيات قابلة للاختبار ونوضح نطاق إثبات الفكرة بصدق.", rtl=True)

    add_heading(doc, "1. المقدمة", 1, rtl=True)
    add_para(doc,
        "يسمح بروتوكول Model Context Protocol (MCP) لتطبيقات الذكاء الاصطناعي بالتعامل مع أدوات وموارد خارجية بطريقة موحدة. ويضيف امتداد "
        "MCP Apps واجهات تفاعلية يقدمها خادم MCP ويعرضها المضيف داخل بيئة معزولة، بدل الاكتفاء بإرجاع النصوص والبيانات (Hou et al., 2025; "
        "Model Context Protocol, 2026b).", rtl=True)
    add_para(doc,
        "يحمي الـ sandbox المضيف من الوصول المباشر إلى صفحته وبياناته، لكن واجهة MCP App تستطيع طلب قدرات ينفذها المضيف، مثل فتح رابط، "
        "أو إرسال رسالة إلى المحادثة، أو تحديث سياق النموذج. لذلك لا تقتصر الحماية على العزل، بل تعتمد أيضًا على القرارات والسياسات التي "
        "يطبقها المضيف على هذه الطلبات (Salomon et al., 2026).", rtl=True)
    add_para(doc,
        "تنبع أهمية الدراسة من أنها تركز على الحد الفاصل بين ما يمنعه العزل تقنيًا وما يجب أن يضبطه المضيف بسياساته. وستقدم الدراسة اختبارًا "
        "عمليًا لهذا الحد، ثم تقارن بين مضيف ملتزم بالمواصفة والمضيف نفسه بعد إضافة طبقة سياسة محددة؛ بما يساعد على تقليل المخاطر مع "
        "المحافظة على الوظائف المشروعة.", rtl=True)

    add_heading(doc, "2. الدراسات السابقة", 1, rtl=True)
    add_para(doc,
        "ركزت دراسات أمن MCP على مخاطر الخوادم والأدوات، وإدارة الصلاحيات، وحقن الأوامر غير المباشر. وأظهرت أن اتصال النماذج بالأدوات قد "
        "يؤدي إلى تنفيذ غير مرغوب أو كشف بيانات إذا لم تضبط الثقة والصلاحيات (Hou et al., 2025; Maloyan & Namiot, 2026; Radosevich & "
        "Halloran, 2025). كما قدمت أعمال AgentDojo وAgentBound أساليب اختبار أمن وفرض حدود التنفيذ، لكنها لم تركز على رسائل واجهة "
        "MCP App إلى المضيف (Bühler et al., 2026; Debenedetti et al., 2024).", rtl=True)
    add_para(doc,
        "أما مواصفة MCP Apps وSEP-1865 فتحددان العزل وCSP ورؤية الأدوات والقنوات التي يديرها المضيف، لكنهما تقدمان متطلبات تصميم لا "
        "مقارنة تجريبية لطبقة تشديد إضافية (Model Context Protocol, 2026b; Salomon et al., 2026).", rtl=True)

    add_heading(doc, "2.1 مقارنة مختصرة للأعمال السابقة", 2, rtl=True)
    add_table(doc,
        ["الباحثون / السنة", "العنوان", "المميزات", "العيوب والفجوات"],
        [
            ["Model Context Protocol؛ Salomon et al. (2026)", "مواصفة MCP Apps وSEP-1865",
             "تحدد البنية الرسمية ونموذج التهديد والضوابط (CSP ورؤية الأدوات والقنوات).",
             "لا تقدمان مقارنة تجريبية قبل سياسة مضيف إضافية وبعدها."],
            ["Maloyan & Namiot (2026)", "Breaking the Protocol",
             "تحليل للمواصفة وتجارب على الحقن والثقة.", "يركز على MCP الأساسي لا القنوات التفاعلية."],
            ["Bühler et al. (2026)", "AgentBound",
             "يفرض سياسات على تنفيذ خوادم MCP.", "يعالج مستوى النظام لا رسائل الواجهة."],
            ["Hou et al. (2025)", "MCP: Landscape, Security Threats, and Future Research Directions",
             "تصنيف واسع لمخاطر MCP ودورة حياة الخادم.", "لا يركز على واجهات MCP Apps وقرارات المضيف."],
            ["Radosevich & Halloran (2025)", "MCP Safety Audit",
             "تدقيق عملي لمخاطر خوادم وأدوات MCP.", "لا يختبر الحد بين واجهة MCP App والمضيف."],
            ["Debenedetti et al. (2024)", "AgentDojo",
             "يقيس الأمن مع الحفاظ على العمل المشروع.", "بيئة عامة للوكلاء وليست لمضيف MCP Apps."],
            ["Greshake et al. (2023)", "Not What You've Signed Up For",
             "يوضح خطر حقن الأوامر غير المباشر.", "ليس مخصصًا لـ MCP Apps."],
        ], rtl=True)

    add_heading(doc, "2.2 الفجوة البحثية", 2, rtl=True)
    add_para(doc,
        "في حدود المصادر التي راجعناها، ركزت الدراسات السابقة على أمن خوادم وأدوات MCP، أو حقن الأوامر وعزل الوكلاء. ولم نجد دراسة تجريبية "
        "مركزة تقارن بين مضيف MCP Apps ملتزم بالمواصفة والمضيف نفسه بعد تفعيل سياسة إضافية للتحكم في القدرات التي يديرها المضيف، مع قياس "
        "الأمن والحفاظ على الوظائف والأداء. يعالج البحث هذه الفجوة ببناء بيئة اختبار قابلة للتكرار ونموذج أولي صغير لطبقة السياسة.", rtl=True)

    add_heading(doc, "3. الغاية والمساهمة", 1, rtl=True)
    add_heading(doc, "3.1 الغاية من البحث", 2, rtl=True)
    add_para(doc,
        "قياس حدود الحماية في MCP Apps عمليًا، وتحديد الفرق بين متطلبات العزل الإلزامية والقرارات التي تعتمد على سياسة المضيف، ثم اختبار "
        "حل أولي يقلل إساءة استخدام القنوات المسموحة.", rtl=True)
    add_heading(doc, "3.2 المساهمة المتوقعة", 2, rtl=True)
    add_bullet(doc, "مجموعة اختبارات قابلة للتكرار تفصل بين اختبارات امتثال المواصفة واختبارات المخاطر المتبقية.", rtl=True)
    add_bullet(doc, "نموذج أولي لطبقة سياسة على جانب المضيف تتحكم في الروابط والرسائل وتحديث سياق النموذج وتوضح مصدر الواجهة.", rtl=True)
    add_bullet(doc, "مقارنة قبل تفعيل الطبقة وبعدها من حيث الأمن، واستمرار الوظائف المشروعة، وزمن المعالجة.", rtl=True)
    add_para(doc,
        "ملاحظة الحداثة: القواعد الفردية (قائمة سماح الروابط، الموافقة الصريحة، إظهار المصدر، حدود الحجم والمعدل، سجل التدقيق) هي ممارسة "
        "جيدة لا اختراعات. عنصرا الحداثة في هذا العمل هما: (أ) القياس التجريبي للمخاطر المتبقية التي تبقى ممكنة عبر قنوات تسمح بها المواصفة "
        "صريحًا، و(ب) علامة حد الثقة المعامَلة كعنصر واجهة قابل للقياس يُقيَّم أثره بدل افتراضه.", rtl=True)

    add_heading(doc, "4. المشاكل البحثية", 1, rtl=True)
    add_heading(doc, "4.1 المشكلة الرئيسية", 2, rtl=True)
    add_para(doc,
        "تعزل MCP Apps الواجهة عن المضيف، لكنها تسمح لها بطلب عمليات ينفذها المضيف. ولا يوجد في الأدبيات التي راجعناها تقييم تجريبي بسيط "
        "يوضح ما تمنعه المواصفة إلزاميًا، وما قد يبقى ممكنًا عبر القنوات المسموحة، ومدى فاعلية سياسة مضيف إضافية في تقليل هذا الخطر.", rtl=True)
    add_heading(doc, "4.2 المشاكل الفرعية", 2, rtl=True)
    add_bullet(doc, "SP1: الحاجة إلى التحقق عمليًا من التزام المضيف بحدود CSP ورؤية الأدوات والموارد.", rtl=True)
    add_bullet(doc, "SP2: احتمال إساءة استخدام القنوات المسموحة مثل ui/open-link وui/message وui/update-model-context من دون كسر الـ sandbox.", rtl=True)
    add_bullet(doc, "SP3: الحاجة إلى معرفة هل تقلل طبقة سياسة إضافية السلوك غير المرغوب من دون تعطيل العمل المشروع أو إضافة عبء زمني كبير.", rtl=True)
    add_heading(doc, "4.3 فرضيات البحث والحل المفترض", 2, rtl=True)
    add_table(doc,
        ["الفرضية القابلة للاختبار", "المشكلة"],
        [
            ["H1: سيرفض المضيف الملتزم بالمواصفة جميع حالات الاختبار المخالفة لـ CSP ورؤية الأدوات والموارد، ويسمح بحالات الامتثال المشروعة. (SP1)", "SP1"],
            ["H2: ستقلل طبقة السياسة المقترحة عدد الإجراءات الحساسة المنفذة دون موافقة، وتمنع انتقال القيمة الاصطناعية عبر قناة غير معتمدة، مقارنة بخط الأساس. (SP2)", "SP2"],
            ["H3: ستحافظ الطبقة على نجاح جميع حالات التحكم المشروعة المحددة مسبقًا، ولن يتجاوز وسيط العبء الإضافي لمعالجة الطلب محليًا 20 مللي ثانية. (SP3)", "SP3"],
        ], rtl=True)
    add_para(doc,
        "توضيح سلوك خط الأساس: المضيف الملتزم بالمواصفة في خط الأساس ينفذ متطلبات الـ MUST الخاصة بالعزل وCSP ورؤية الأدوات والموارد، "
        "لكنه لا يصدر مطالبة موافقة إلزامية على ui/open-link أو ui/message أو ui/update-model-context. وفي غياب طبقة السياسة، يُرسل هذه "
        "الطلبات وفق المعالجة الافتراضية للمواصفة (يفتح الرابط الخارجي، يوصل الرسالة إلى المحادثة، يحدث سياق النموذج). هذه المعالجة "
        "الافتراضية هي بالضبط سطح الخطر المتبقي الذي تستهدفه طبقة السياسة.", rtl=True)
    add_para(doc,
        "الحل المفترض: طبقة داخل المضيف تعترض الطلبات الحساسة قبل تنفيذها وتطبق قائمة سماح للروابط، وموافقة صريحة، وإظهار مصدر الواجهة، "
        "وحدودًا للحجم ومعدل الطلبات، وسجل تدقيق. تقبل الفرضيات أو ترفض وفق النتائج الفعلية، ولا تفترض الدراسة نجاح الحل مسبقًا.", rtl=True)

    add_heading(doc, "5. أهمية البحث وأهدافه", 1, rtl=True)
    add_heading(doc, "5.1 أهمية البحث", 2, rtl=True)
    add_para(doc,
        "يوضح البحث مسؤولية المضيف عند التعامل مع واجهة يقدمها خادم غير موثوق، ويمنع الخلط بين حماية الـ sandbox وحماية سياسات المضيف. "
        "كما يقدم اختبارًا ونموذجًا أوليًا يمكن لمطوري مضيفات MCP إعادة استخدامهما.", rtl=True)
    add_heading(doc, "5.2 الهدف العام", 2, rtl=True)
    add_para(doc, "تقييم حدود الثقة في MCP Apps وبناء طبقة سياسة صغيرة على جانب المضيف وقياس أثرها تجريبيًا.", rtl=True)
    add_heading(doc, "5.3 الأهداف الفرعية", 2, rtl=True)
    add_bullet(doc, "استخراج المتطلبات الأمنية الإلزامية والقنوات التي تعتمد على سياسة المضيف.", rtl=True)
    add_bullet(doc, "بناء مختبر محلي وتنفيذ خط أساس موحد وسيناريوهات قابلة للتكرار.", rtl=True)
    add_bullet(doc, "تنفيذ طبقة السياسة المقترحة وتشغيل السيناريوهات نفسها بعد تفعيلها.", rtl=True)
    add_bullet(doc, "مقارنة الأمن والوظائف والأداء وقبول الفرضيات أو رفضها وفق النتائج.", rtl=True)

    add_heading(doc, "6. المنهجية", 1, rtl=True)
    add_heading(doc, "6.1 نوع الدراسة وتصميمها", 2, rtl=True)
    add_para(doc, "تستخدم الدراسة منهجًا تجريبيًا تطبيقيًا داخل مختبر محلي معزول. وتنفذ الحالات نفسها في مجموعتين:", rtl=True)
    add_bullet(doc, "Baseline: مضيف اختبار يطبق متطلبات MUST في مواصفة MCP Apps، دون طبقة السياسة الإضافية.", rtl=True)
    add_bullet(doc, "Treatment: المضيف نفسه والبيئة نفسها، مع تفعيل الطبقة المقترحة فقط.", rtl=True)
    add_para(doc,
        "المتغير المستقل هو حالة الطبقة (معطلة/مفعلة). والمتغيرات التابعة هي قرارات السماح والرفض، وتنفيذ الإجراءات دون موافقة، ووصول "
        "البيانات الاصطناعية، ونجاح الوظائف المشروعة، وزمن المعالجة.", rtl=True)
    add_heading(doc, "6.2 بيئة الاختبار ونطاقه", 2, rtl=True)
    add_bullet(doc, "جهاز Linux واحد وبيئة محلية معزولة.", rtl=True)
    add_bullet(doc, "مضيف اختبار واحد مبني على basic-host وAppBridge من مشروع ext-apps (Model Context Protocol, 2026a).", rtl=True)
    add_bullet(doc, "خادم MCP محلي، وواجهة مشروعة، وواجهة اختبار غير موثوقة.", rtl=True)
    add_bullet(doc, "أدوات وموارد وهمية، وخادم استقبال محلي، وقيمة اختبار مثل SYNTHETIC_SECRET_001.", rtl=True)
    add_bullet(doc, "سجل موحد لرسائل JSON-RPC وقرارات السياسة والأزمنة.", rtl=True)
    add_para(doc,
        "يُفترض أن المهاجم يتحكم في خادم MCP والواجهة، لكنه لا يملك وصولًا مباشرًا إلى جهاز المستخدم. ولا تشمل الدراسة كسر المتصفح أو "
        "الهروب من الـ sandbox أو إجراء تجربة تصيد على أشخاص حقيقيين.", rtl=True)
    add_heading(doc, "6.3 الحل المقترح", 2, rtl=True)
    add_para(doc, "تعترض طبقة السياسة رسائل الواجهة قبل تنفيذها، وتطبق أربع قواعد:", rtl=True)
    add_bullet(doc, "1. الروابط: التحقق من مخطط البروتوكول (http/https) وموافقة صريحة قبل فتح الرابط.", rtl=True)
    add_bullet(doc, "2. الرسائل والسياق: موافقة صريحة، وإظهار شارة المصدر، وحد أقصى لحجم الرسالة (4 كيلوبايت).", rtl=True)
    add_bullet(doc, "3. حد الثقة المرئي: إضافة علامة ثابتة حول الواجهة توضح أنها مقدمة من خادم MCP خارجي.", rtl=True)
    add_bullet(doc, "4. التدقيق: تسجيل المصدر ونوع الطلب والقرار وسببه وزمن المعالجة دون تخزين بيانات حساسة.", rtl=True)
    add_para(doc,
        "تظل اختبارات CSP ورؤية الأدوات جزءًا من امتثال خط الأساس للمواصفة، وليست إسهامًا جديدًا للطبقة. والعنصر الجديد المُقيَّم هنا هو "
        "علامة حد الثقة المعامَلة كعنصر قابل للقياس والقياس التجريبي للمخاطر المتبقية عبر القنوات المسموحة.", rtl=True)
    add_heading(doc, "6.4 خطوات التنفيذ", 2, rtl=True)
    add_bullet(doc, "1. تشغيل المثال الرسمي والتحقق من عرض واجهة مشروعة واستدعاء أداة مسموحة.", rtl=True)
    add_bullet(doc, "2. بناء الخادم المحلي والواجهتين والأدوات والموارد الوهمية وخادم الاستقبال.", rtl=True)
    add_bullet(doc, "3. تثبيت حالات الاختبار وتشغيلها في Baseline وتسجيل النتائج.", rtl=True)
    add_bullet(doc, "4. تنفيذ طبقة السياسة كوحدة يمكن تشغيلها وإيقافها.", rtl=True)
    add_bullet(doc, "5. تشغيل الحالات نفسها في Treatment بالإعدادات والبيانات نفسها.", rtl=True)
    add_bullet(doc, "6. مقارنة النتائج واختبار H1-H3 وكتابة الاستنتاجات.", rtl=True)
    add_heading(doc, "6.5 مصفوفة الاختبار", 2, rtl=True)
    add_table(doc,
        ["الاختبار", "Baseline (المتوقع)", "Treatment (المتوقع)", "المقياس"],
        [
            ["أداة مشروعة ذات وصول app", "سماح", "سماح", "الحفاظ على الوظيفة"],
            ["أداة غير ظاهرة للتطبيق", "رفض", "رفض", "امتثال المواصفة"],
            ["اتصال إلى نطاق غير معلن في CSP", "رفض", "رفض", "امتثال CSP"],
            ["فتح رابط خارجي", "بلا مطالبة موافقة؛ يُفتح الرابط وفق المعالجة الافتراضية (يُرصد ويسجل)", "موافقة ثم سماح/رفض", "التنفيذ دون موافقة"],
            ["ui/message أو تحديث السياق للمضيف", "يُوصل بلا مؤشر مصدر (يُرصد ويسجل)", "موافقة وإظهار المصدر", "سلامة القناة"],
            ["واجهة تشبه المضيف", "تعرض داخل العزل", "تظهر معها علامة مصدر ثابتة", "وضوح حد الثقة"],
            ["عملية مشروعة محددة مسبقًا", "نجاح", "نجاح", "الحجب الخاطئ"],
        ], rtl=True)
    add_para(doc,
        "نحن ندرس ثلاث فئات من القدرات التي يديرها المضيف: (1) فتح الروابط (ui/open-link)، (2) الرسائل وتحديث سياق النموذج (ui/message و"
        "ui/update-model-context)، و(3) التدقيق والمراقبة. ويضع اختبار التسريب SYNTHETIC_SECRET_001 في جسم ui/message وفي حمولة "
        "ui/update-model-context ويتحقق مما إذا كانت تصل إلى خادم الاستقبال المحلي.", rtl=True)
    add_heading(doc, "6.6 القياس وتحليل النتائج", 2, rtl=True)
    add_bullet(doc, "عدد اختبارات الامتثال الناجحة من الإجمالي.", rtl=True)
    add_bullet(doc, "عدد الطلبات الحساسة المنفذة دون موافقة قبل الطبقة وبعدها.", rtl=True)
    add_bullet(doc, "نجاح أو فشل انتقال القيمة الاصطناعية في كل قناة.", rtl=True)
    add_bullet(doc, "نسبة العمليات المشروعة الناجحة، وعدد العمليات المحجوبة خطأ.", rtl=True)
    add_bullet(doc, "اكتمال سجل التدقيق ومتوسط ووسيط زمن المعالجة عند الشريحة المئوية 95.", rtl=True)
    add_para(doc,
        "خطة قبول الفرضيات: تُقبل H1 إذا رفض خط الأساس 100% من حالات مخالفة CSP وعدم ظهور الأدوات وأسمح بـ 100% من حالات الامتثال "
        "المشروعة، وإلا تُرفض. تُقبل H2 إذا قللت المعالجة الإجراءات الحساسة دون موافقة إلى الصفر ومنعت انتقال SYNTHETIC_SECRET_001 عبر "
        "ui/message وui/update-model-context، وإلا تُرفض. تُقبل H3 إذا نجحت جميع حالات التحكم المشروعة في المعالجة ولم يتجاوز وسيط عبء "
        "السياسة المحلي 20 مللي ثانية، وإلا تُرفض.", rtl=True)
    add_para(doc,
        "تشغل كل حالة وظيفية خمس مرات في كل مجموعة. ويُكرر قياس الأداء 30 مرة بعد خمس عمليات إحماء لا تدخل في الحساب. تعرض النتائج "
        "بالأعداد والنسب المئوية والمللي ثانية، ثم تقارن بالنتائج المتوقعة في H1-H3. وتمثل 20 مللي ثانية عتبة تشغيلية أولية حددها الباحثون "
        "لتقييم النموذج داخل المختبر، وليست حدًا معياريًا في مواصفة MCP Apps.", rtl=True)
    add_heading(doc, "6.7 الضوابط الأخلاقية والقيود", 2, rtl=True)
    add_para(doc,
        "تُجرى جميع التجارب محليًا باستخدام بيانات وحسابات اصطناعية، ولا تستهدف خدمات عامة أو مستخدمين حقيقيين. تقتصر النتائج على مضيف "
        "واحد وثلاث فئات من القدرات؛ لذلك يمثل النموذج إثبات فكرة وليس منتجًا أمنيًا مكتملًا.", rtl=True)

    add_heading(doc, "7. تنظيم الوقت", 1, rtl=True)
    add_para(doc, "مدة تنفيذ البحث ستة أسابيع.", rtl=True)
    add_table(doc,
        ["الفترة", "العمل الرئيسي", "المخرج", "التكلفة المباشرة"],
        [
            ["الأسبوع 1", "مراجعة المواصفة؛ تشغيل المثال الرسمي؛ تثبيت خطة الاختبار.", "مختبر يعمل وخطة اختبار ثابتة", "0"],
            ["الأسبوع 2", "بناء الواجهتين؛ تشغيل حالات Baseline.", "نتائج خط الأساس", "0"],
            ["الأسبوع 3", "إكمال قياسات خط الأساس وتثبيت سجلاته.", "نتائج خط أساس نهائية", "0"],
            ["الأسبوع 4", "تنفيذ طبقة السياسة كوحدة قابلة للتشغيل.", "وحدة طبقة السياسة", "0"],
            ["الأسبوع 5", "تشغيل الحالات نفسها في Treatment.", "نتائج ما بعد الحل", "0"],
            ["الأسبوع 6", "تحليل النتائج؛ اختبار H1-H3؛ كتابة التقرير.", "التقرير النهائي", "0"],
        ], rtl=True)
    add_para(doc,
        "لا توجد تكلفة مباشرة متوقعة؛ لأن الجهاز متاح والأدوات مفتوحة المصدر والتجارب محلية. وإذا ظهرت تكلفة طارئة فستوثق في التقرير الفعلي.", rtl=True)

    add_heading(doc, "8. المراجع", 1, rtl=True)
    refs = [
        "Bühler, C., Biagiola, M., Di Grazia, L., & Salvaneschi, G. (2026). AgentBound: Securing execution boundaries of AI agents. Proceedings of the 34th ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering. https://doi.org/10.1145/3808103",
        "Debenedetti, E., Zhang, J., Balunović, M., Beurer-Kellner, L., Fischer, M., & Tramèr, F. (2024). AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses in LLM agents. NeurIPS 2024 Datasets and Benchmarks Track. https://arxiv.org/abs/2406.13352",
        "Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection. Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security. https://arxiv.org/abs/2302.12173",
        "Hou, X., Zhao, Y., Wang, S., & Wang, H. (2025). Model Context Protocol (MCP): Landscape, security threats, and future research directions. arXiv:2503.23278. https://arxiv.org/abs/2503.23278",
        "Maloyan, N., & Namiot, D. (2026). Breaking the Protocol: Security analysis of the Model Context Protocol specification and prompt injection vulnerabilities in tool-integrated LLM agents. arXiv:2601.17549. https://arxiv.org/abs/2601.17549",
        "Model Context Protocol. (2026a). ext-apps: Specification and SDK for the MCP Apps extension [Source code]. https://github.com/modelcontextprotocol/ext-apps",
        "Model Context Protocol. (2026b). MCP Apps specification (revision 2026-01-26). https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx",
        "Radosevich, B., & Halloran, J. (2025). MCP safety audit: LLMs with the Model Context Protocol allow major security exploits. arXiv:2504.03767. https://arxiv.org/abs/2504.03767",
        "Salomon, I., Yosef, L., Chafik, O., Swannack, J., Hefner, J., Pidkuiko, A., Cooper, N., Ashley, B., & Christakis, A. (2026). SEP-1865: MCP Apps—Interactive user interfaces for MCP. Model Context Protocol. https://modelcontextprotocol.io/seps/1865-mcp-apps-interactive-user-interfaces-for-mcp",
    ]
    for r in refs:
        p = doc.add_paragraph(r)
        p.paragraph_format.left_indent = Pt(18)
        p.paragraph_format.first_line_indent = Pt(-18)

    doc.save(f"{W}/MCP_Apps_Trust_Boundaries_Proposal_AR.docx")
    print("AR saved")

build_en()
build_ar()
