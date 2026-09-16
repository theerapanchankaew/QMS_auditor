// MASCI Audit Report Renderer v1.0
// Generates org-branded DOCX from structured JSON struct
// Usage: node build_report.js [input.json]

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak,
  TabStopType, TabStopPosition, LevelFormat
} = require('docx');
const fs = require('fs');

// ── Color palette (MASCI brand) ──────────────────────────────────────────────
const BRAND = {
  navy:    '1F3864',  // Section A header bg
  teal:    '1F7B8C',  // Section headers
  blue:    '2E75B6',  // Table headers
  lightBg: 'D9E2F3',  // Light blue row bg
  grayBg:  'F2F2F2',  // Alternate row bg
  white:   'FFFFFF',
  black:   '000000',
  darkGray:'404040',
};

// ── DXA / layout constants (A4 portrait) ─────────────────────────────────────
const PAGE_W   = 11906;
const MARGIN   = 1080;   // 0.75 inch margins
const CONTENT_W = PAGE_W - MARGIN * 2;  // 9746 DXA

// ── Helper: thin border ───────────────────────────────────────────────────────
const thin  = { style: BorderStyle.SINGLE, size: 4, color: 'AAAAAA' };
const thick = { style: BorderStyle.SINGLE, size: 8, color: BRAND.blue };
const none  = { style: BorderStyle.NIL };
const borders = (t=thin,b=thin,l=thin,r=thin) => ({ top:t, bottom:b, left:l, right:r });
const allThin  = () => borders();
const topBottom = () => borders(thin, thin, none, none);

// ── Helper: cell ─────────────────────────────────────────────────────────────
function cell(children, { w, fill, bold=false, align=AlignmentType.LEFT, vAlign=VerticalAlign.TOP, colspan=1, brd=allThin() } = {}) {
  if (!Array.isArray(children)) children = [children];
  return new TableCell({
    borders: brd,
    columnSpan: colspan,
    verticalAlign: vAlign,
    width: w ? { size: w, type: WidthType.DXA } : { size: 0, type: WidthType.AUTO },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: children.map(c => typeof c === 'string'
      ? new Paragraph({ alignment: align, children: [new TextRun({ text: c, bold, size: 18, font: 'Arial' })] })
      : c
    ),
  });
}

// ── Helper: para ─────────────────────────────────────────────────────────────
function para(text, { bold=false, size=18, color=BRAND.black, spacing={after:80}, align=AlignmentType.LEFT } = {}) {
  return new Paragraph({
    alignment: align,
    spacing,
    children: [new TextRun({ text, bold, size, font: 'Arial', color })],
  });
}

function spacer(n=1) {
  return Array.from({length:n}, () => para('', { spacing: { after: 0, before: 0 }, size: 14 }));
}

// ── Section heading (colored bar) ────────────────────────────────────────────
function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 200, after: 100 },
    shading: { fill: BRAND.teal, type: ShadingType.CLEAR },
    children: [new TextRun({ text, bold: true, size: 22, font: 'Arial', color: BRAND.white })],
    indent: { left: 120, right: 120 },
  });
}

// ── Report title block ────────────────────────────────────────────────────────
function buildTitleBlock(data) {
  const a = data.section_a;
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 60 },
      children: [new TextRun({ text: a.client_name_th, bold: true, size: 28, font: 'Arial' })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 80 },
      children: [new TextRun({ text: a.client_name_en, bold: true, size: 24, font: 'Arial', color: BRAND.teal })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 60 },
      children: [new TextRun({ text: 'Audit Report', bold: true, size: 36, font: 'Arial' })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: a.audit_date, size: 20, font: 'Arial', color: BRAND.darkGray })],
    }),
  ];
}

// ── Contents table ────────────────────────────────────────────────────────────
function buildContents() {
  const rows = [
    ['Section A: Client Information',    '1'],
    ['Section B: Audit summary',         '2'],
    ['Section C: Summary of finding',    '3'],
    ['Section D: Auditor recommendation','5'],
    ['Section E: Audit programme',       '5'],
  ];
  return [
    para('Contents', { bold: true, size: 22, spacing: { before: 100, after: 80 } }),
    ...rows.map(([label, pg]) =>
      new Paragraph({
        spacing: { after: 60 },
        tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        children: [
          new TextRun({ text: `  ${label}`, bold: true, size: 18, font: 'Arial' }),
          new TextRun({ text: `\t${pg}`, size: 18, font: 'Arial' }),
        ],
      })
    ),
    ...spacer(1),
    para('Attachment', { bold: true, size: 20, spacing: { before: 80, after: 60 } }),
    ...['Audit Result','Previous nonconformity report','Nonconformity report','Audit schedule','Certificate confirmation'].map(
      t => new Paragraph({
        spacing: { after: 40 },
        numbering: { reference: 'bullets', level: 0 },
        children: [new TextRun({ text: t, size: 18, font: 'Arial' })],
      })
    ),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ── Section A ─────────────────────────────────────────────────────────────────
function buildSectionA(a) {
  // ── Client info table ──
  const reps = a.client_representatives.map(r => `${r.name}  ${r.position}`).join('\n');
  const team = a.audit_team.map(r => `${r.name}  ${r.role}`).join('\n');

  function multilineCell(lines, w, fill) {
    return new TableCell({
      borders: allThin(),
      width: { size: w, type: WidthType.DXA },
      shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: lines.split('\n').map(l =>
        new Paragraph({ children: [new TextRun({ text: l, size: 18, font: 'Arial' })] })
      ),
    });
  }

  const hdrCell = (txt, w) => cell(txt, { w, fill: BRAND.lightBg, bold: true });

  const clientTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [2400, 5600, 980, 770],
    rows: [
      new TableRow({ children: [
        hdrCell('Client name:', 2400),
        new TableCell({
          borders: allThin(), columnSpan: 3,
          width: { size: 7350, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [
            new Paragraph({ children: [new TextRun({ text: a.client_name_th, bold: true, size: 18, font: 'Arial' })] }),
            new Paragraph({ children: [new TextRun({ text: a.client_name_en, size: 18, font: 'Arial' })] }),
          ],
        }),
      ]}),
      new TableRow({ children: [
        hdrCell('Address (Premise):', 2400),
        new TableCell({
          borders: allThin(), width: { size: 5600, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [
            new Paragraph({ children: [new TextRun({ text: a.address_th, size: 18, font: 'Arial' })] }),
            new Paragraph({ children: [new TextRun({ text: a.address_en, size: 18, font: 'Arial' })] }),
          ],
        }),
        cell(a.audit_mode, { w: 980, fill: BRAND.grayBg }),
        cell(a.site_type,  { w: 770, fill: BRAND.grayBg }),
      ]}),
      new TableRow({ children: [
        hdrCell('Audit date:', 2400),
        multilineCell(a.audit_date, 5600, null),
        cell('', { w: 980 }), cell('', { w: 770 }),
      ]}),
      new TableRow({ children: [
        hdrCell("Client's representative:", 2400),
        new TableCell({
          borders: allThin(), width: { size: 5600, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: a.client_representatives.map(r =>
            new Paragraph({ children: [new TextRun({ text: r.name, size: 18, font: 'Arial' })] })
          ),
        }),
        new TableCell({
          borders: allThin(), columnSpan: 2, width: { size: 1750, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: a.client_representatives.map(r =>
            new Paragraph({ children: [new TextRun({ text: r.position, size: 18, font: 'Arial' })] })
          ),
        }),
      ]}),
      new TableRow({ children: [
        hdrCell('Audit team:', 2400),
        new TableCell({
          borders: allThin(), width: { size: 5600, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: a.audit_team.map(r =>
            new Paragraph({ children: [new TextRun({ text: r.name, size: 18, font: 'Arial' })] })
          ),
        }),
        new TableCell({
          borders: allThin(), columnSpan: 2, width: { size: 1750, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: a.audit_team.map(r =>
            new Paragraph({ children: [new TextRun({ text: r.role, size: 18, font: 'Arial' })] })
          ),
        }),
      ]}),
      new TableRow({ children: [
        hdrCell('No. of employees applied to the scope:', 2400),
        cell(`${a.num_employees_in_scope} คน`, { w: 5600 }),
        cell('', { w: 980 }), cell('', { w: 770 }),
      ]}),
    ],
  });

  // ── Management system table ──
  const msHdr = ['Application no.','Certification no.','Expired date','Standard applied:','Audit program','Certification application'];
  const msWidths = [1700,1700,1500,2200,1100,1546];

  const msTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: msWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: msHdr.map((h, i) => cell(h, { w: msWidths[i], fill: BRAND.blue, bold: true })),
      }),
      ...a.management_systems.map(ms =>
        new TableRow({ children: [
          cell(ms.application_no,            { w: msWidths[0] }),
          cell(ms.certification_no,           { w: msWidths[1] }),
          cell(ms.expired_date,               { w: msWidths[2] }),
          cell(ms.standard,                   { w: msWidths[3] }),
          cell(ms.audit_program,              { w: msWidths[4] }),
          cell(ms.certification_application,  { w: msWidths[5] }),
        ]})
      ),
    ],
  });

  // ── Certified scope table ──
  const scopeHdr = ['MS','site','Scope applied','ISIC/IAF code'];
  const scopeW   = [600, 700, 7000, 1446];
  const scopeTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: scopeW,
    rows: [
      new TableRow({
        tableHeader: true,
        children: scopeHdr.map((h, i) => cell(h, { w: scopeW[i], fill: BRAND.blue, bold: true })),
      }),
      ...a.certified_scope.map(s =>
        new TableRow({ children: [
          cell(s.ms, { w: scopeW[0] }),
          cell(s.site, { w: scopeW[1] }),
          new TableCell({
            borders: allThin(), width: { size: scopeW[2], type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [
              new Paragraph({ children: [new TextRun({ text: s.scope_th, size: 18, font: 'Arial' })] }),
              new Paragraph({ children: [new TextRun({ text: s.scope_en, size: 18, font: 'Arial' })] }),
            ],
          }),
          cell(s.isic_iaf_code, { w: scopeW[3] }),
        ]})
      ),
      new TableRow({ children: [
        new TableCell({
          borders: allThin(), columnSpan: 4, width: { size: CONTENT_W, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [
            new TextRun({ text: 'Appropriateness of the scope certified:  ', bold: true, size: 18, font: 'Arial' }),
            new TextRun({ text: a.scope_appropriateness || 'Suitable', size: 18, font: 'Arial' }),
          ]})],
        }),
      ]}),
    ],
  });

  // ── Audit Objectives ──
  const objParagraphs = a.audit_objectives.map(obj =>
    new Paragraph({
      spacing: { after: 60 },
      numbering: { reference: 'checkboxes', level: 0 },
      children: [new TextRun({ text: obj, size: 18, font: 'Arial' })],
    })
  );

  const critParagraphs = a.audit_criteria.map(crit =>
    new Paragraph({
      spacing: { after: 60 },
      numbering: { reference: 'bullets', level: 0 },
      children: [new TextRun({ text: crit, size: 18, font: 'Arial' })],
    })
  );

  return [
    sectionHeading('Section A:  Client Information'),
    ...spacer(1),
    clientTable,
    ...spacer(1),
    para('Management system applied:', { bold: true, size: 20 }),
    ...spacer(1),
    msTable,
    ...spacer(1),
    para('Certified scope:', { bold: true, size: 20 }),
    ...spacer(1),
    scopeTable,
    ...spacer(1),
    para('Audit Objectives:', { bold: true, size: 20 }),
    ...objParagraphs,
    ...spacer(1),
    para('Audit criteria and Reference documents:', { bold: true, size: 20 }),
    ...critParagraphs,
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ── Section B ─────────────────────────────────────────────────────────────────
function buildSectionB(b) {
  function statusLine(label, value, detail='') {
    return new Paragraph({
      spacing: { after: 80 },
      children: [
        new TextRun({ text: `${label}  `, bold: true, size: 18, font: 'Arial' }),
        new TextRun({ text: value, size: 18, font: 'Arial' }),
        detail ? new TextRun({ text: `  ${detail}`, size: 18, font: 'Arial', color: BRAND.darkGray }) : new TextRun(''),
      ],
    });
  }

  const ncStatus = b.nonconformities_found
    ? `Nonconformity(ies)  —  Major: ${b.num_major_nc}  |  Minor: ${b.num_minor_nc}`
    : 'No Nonconformities';

  return [
    sectionHeading('Section B:  Audit summary'),
    ...spacer(1),
    statusLine('Audit result:', ncStatus, b.ofi_found ? '  OFI: found (see attachment)' : ''),
    statusLine('Deviation from plan:', b.deviation_from_plan ? `Yes — ${b.deviation_detail}` : 'No deviation from the plan'),
    statusLine('Significant changes:', b.significant_changes ? 'Yes' : 'No any change',
      b.significant_changes && b.changes_detail ? JSON.stringify(b.changes_detail) : ''),
    statusLine('Effectiveness of CA from previous audit:',
      b.ca_effectiveness?.no_previous_nc ? 'No nonconformity in previous audit'
        : `${b.ca_effectiveness?.effective_items||0} effective / ${b.ca_effectiveness?.not_effective_items||0} not effective`),
    statusLine('Certification mark use:',
      b.certification_mark_use?.in_use ? 'In use' : 'Not in use',
      b.certification_mark_use?.status + (b.certification_mark_use?.detail ? `  —  ${b.certification_mark_use.detail}` : '')),
    statusLine('Unresolved diverging opinions:', b.unresolved_diverging_opinions ? `Yes — ${b.unresolved_detail}` : 'No unresolved issues'),
    statusLine('Significant issues impacting audit programme:', b.significant_issues_for_audit_programme
      ? `Yes — ${b.significant_issues_detail}` : 'No significant issues'),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ── Section C ─────────────────────────────────────────────────────────────────
function buildSectionC(c) {
  const VERDICT_FILL = { 'Effective': BRAND.grayBg, 'Minor NC': 'FFEEBA', 'Major NC': 'F8CECC' };

  const findingRows = c.findings.map(f => {
    const fill = VERDICT_FILL[f.verdict] || BRAND.white;
    return new TableRow({ children: [
      new TableCell({
        borders: allThin(),
        width: { size: 7500, type: WidthType.DXA },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [
          new Paragraph({ children: [new TextRun({ text: f.category, bold: true, size: 18, font: 'Arial' })] }),
          f.category_description
            ? new Paragraph({ children: [new TextRun({ text: f.category_description, size: 16, font: 'Arial', color: BRAND.darkGray })] })
            : null,
          new Paragraph({ spacing: { before: 60 }, children: [new TextRun({ text: 'Summary: ', bold: true, size: 18, font: 'Arial' })] }),
          ...f.summary.split('\n').map(line =>
            new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: line, size: 18, font: 'Arial' })] })
          ),
        ].filter(Boolean),
      }),
      cell(f.verdict, { w: 2246, fill, bold: f.verdict !== 'Effective', align: AlignmentType.CENTER, vAlign: VerticalAlign.CENTER }),
    ]});
  });

  return [
    sectionHeading('Section C:  Summary of finding'),
    ...spacer(1),
    para(c.audit_type, { bold: true, size: 20, spacing: { after: 100 } }),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: [7500, 2246],
      rows: [
        new TableRow({
          tableHeader: true,
          children: [
            cell('Finding area & summary', { w: 7500, fill: BRAND.blue, bold: true }),
            cell('Result', { w: 2246, fill: BRAND.blue, bold: true, align: AlignmentType.CENTER }),
          ],
        }),
        ...findingRows,
      ],
    }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ── Section D ─────────────────────────────────────────────────────────────────
function buildSectionD(d) {
  const isMaintain = d.recommendation_type === 'maintain';

  const recText = isMaintain
    ? 'The audit was completely conducted according to the audit plan and objectives. Based on the objective evidence and finding above (Section B & C) together with the capability of the management system that can meet applicable requirements and expected outcomes. The audit team will:\n\n• Send copy of nonconformity report(s) to the organization\'s representative. The corrective action plan is requested to be submitted to audit team to verify its effectiveness and then later submitted to the Review Panel. Following up of the proposed corrective actions will be conducted in the next audit;\n\n• Report to the Review Panel/Technical reviewer to:'
    : 'The audit was completely conducted according to the audit plan and objectives. Based on the objective evidence and finding above (Section B & C). The audit team will:\n\n• Send the copy of the nonconformity report(s) to the organization\'s representative. The corrective action plan is requested to submit to the audit team to verify its effectiveness. Follow up the corrective action will be conducted within 6 months from the date of this audit.\n\n• Unless the proposed corrective action is effectively implemented, the assessment of the whole system will be required.';

  const msLines = d.recommendations_by_ms.map(r =>
    new Paragraph({
      spacing: { after: 60 },
      numbering: { reference: 'bullets', level: 0 },
      children: [new TextRun({ text: `${r.ms}: ${r.recommendation}`, size: 18, font: 'Arial' })],
    })
  );

  const contentCell = new TableCell({
    borders: allThin(),
    width: { size: CONTENT_W, type: WidthType.DXA },
    margins: { top: 120, bottom: 120, left: 160, right: 160 },
    children: [
      ...recText.split('\n\n').map(block =>
        new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: block.replace(/^• /, ''), size: 18, font: 'Arial' })] })
      ),
      ...msLines,
    ],
  });

  return [
    sectionHeading('Section D:  Auditor recommendation'),
    ...spacer(1),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: [CONTENT_W],
      rows: [ new TableRow({ children: [contentCell] }) ],
    }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ── Section E ─────────────────────────────────────────────────────────────────
function buildSectionE(e) {
  const progHdr  = ['Audit plan','Audit date','QMS','EMS','OHSMS','Duration'];
  const progW    = [2000, 2200, 1400, 1400, 1400, 1346];

  const progTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: progW,
    rows: [
      new TableRow({
        tableHeader: true,
        children: ['Audit plan','Audit date','QMS','EMS','OHSMS','Duration'].map((h,i) =>
          cell(h, { w: progW[i], fill: BRAND.blue, bold: true, align: AlignmentType.CENTER })
        ),
      }),
      ...e.audit_programme_rows.map(row =>
        new TableRow({ children: [
          cell(row.year_label,  { w: progW[0], align: AlignmentType.CENTER }),
          cell(row.audit_date,  { w: progW[1], align: AlignmentType.CENTER }),
          cell(row.qms_stage,   { w: progW[2], align: AlignmentType.CENTER }),
          cell(row.ems_stage,   { w: progW[3], align: AlignmentType.CENTER }),
          cell(row.ohsms_stage, { w: progW[4], align: AlignmentType.CENTER }),
          cell(row.duration_md, { w: progW[5], align: AlignmentType.CENTER }),
        ]})
      ),
    ],
  });

  // Remark
  const remark = para(`Remark: ${e.remark || 'Reassessment audit will be done 60 days before certificate expires.'}`,
    { size: 16, color: BRAND.darkGray, spacing: { after: 160 } });

  // Clause coverage tables
  const clauseTables = [];
  for (const std of (e.clause_coverage || [])) {
    const cW = [4200, 3200, 700, 700, 700, 246];
    clauseTables.push(
      para(`${std.standard} Requirement Clause Coverage`, { bold: true, size: 20, spacing: { before: 200, after: 80 } }),
      new Table({
        width: { size: CONTENT_W, type: WidthType.DXA },
        columnWidths: cW,
        rows: [
          new TableRow({
            tableHeader: true,
            children: ['Clause','Title','Stg.2/re','Surv#1','Surv#2','-'].map((h,i) =>
              cell(h, { w: cW[i], fill: BRAND.blue, bold: true, align: AlignmentType.CENTER })
            ),
          }),
          ...(std.clauses || []).map((cl, idx) => {
            const isGroupHdr = /^\d+$/.test(cl.clause_no);
            const fill = isGroupHdr ? BRAND.lightBg : (idx%2===0 ? BRAND.white : BRAND.grayBg);
            return new TableRow({ children: [
              cell(cl.clause_no, { w: cW[0], fill, bold: isGroupHdr }),
              cell(cl.clause_title, { w: cW[1], fill, bold: isGroupHdr }),
              cell(cl.na ? 'NA' : (cl.stg2_re || ''), { w: cW[2], fill, align: AlignmentType.CENTER }),
              cell(cl.na ? 'NA' : (cl.surv1 || ''), { w: cW[3], fill, align: AlignmentType.CENTER }),
              cell(cl.na ? 'NA' : (cl.surv2 || ''), { w: cW[4], fill, align: AlignmentType.CENTER }),
              cell('', { w: cW[5], fill }),
            ]});
          }),
        ],
      }),
      ...spacer(1),
    );
  }

  // Signature block
  const sigW = Math.floor(CONTENT_W / Math.max(e.signatories.length, 1));
  const sigCells = e.signatories.map(s =>
    new TableCell({
      borders: borders(none, none, none, none),
      width: { size: sigW, type: WidthType.DXA },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `( ${s.name} )`, size: 18, font: 'Arial' })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: s.role, size: 18, font: 'Arial' })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: s.date, size: 18, font: 'Arial' })] }),
      ],
    })
  );

  const sigTable = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: Array(e.signatories.length).fill(sigW),
    rows: [ new TableRow({ children: sigCells }) ],
  });

  return [
    sectionHeading('Section E:  Audit programme'),
    ...spacer(1),
    progTable,
    remark,
    ...clauseTables,
    ...spacer(2),
    sigTable,
    ...spacer(1),
    para(`Remark: ${e.remark || 'The audit conclusion is based on a sampling process of the available data during the audit.'}`,
      { size: 16, color: BRAND.darkGray }),
  ];
}

// ── Build document ────────────────────────────────────────────────────────────
async function buildDocument(data) {
  const a = data.section_a;
  const m = data.meta;

  // Header
  const header = new Header({
    children: [
      new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND.teal, space: 1 } },
        spacing: { after: 80 },
        tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        children: [
          new TextRun({ text: a.client_name_th || 'MASCI Audit Report', bold: true, size: 18, font: 'Arial', color: BRAND.teal }),
          new TextRun({ text: '\tAudit Report', size: 16, font: 'Arial', color: BRAND.darkGray }),
        ],
      }),
    ],
  });

  // Footer
  const footer = new Footer({
    children: [
      new Paragraph({
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: BRAND.teal, space: 1 } },
        spacing: { before: 60 },
        tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        children: [
          new TextRun({ text: `${m.form_ref}  ${m.issue}, ${m.revision}  ${m.issue_date}`, size: 16, font: 'Arial', color: BRAND.darkGray }),
          new TextRun({ text: '\t', size: 16 }),
          new TextRun({ text: 'Page ', size: 16, font: 'Arial', color: BRAND.darkGray }),
          new TextRun({ children: [PageNumber.CURRENT], size: 16, font: 'Arial', color: BRAND.darkGray }),
          new TextRun({ text: '     CONFIDENTIAL', bold: true, size: 16, font: 'Arial', color: BRAND.teal }),
        ],
      }),
    ],
  });

  const doc = new Document({
    numbering: {
      config: [
        { reference: 'bullets', levels: [
          { level: 0, format: LevelFormat.BULLET, text: '\u2022',
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } }
        ]},
        { reference: 'checkboxes', levels: [
          { level: 0, format: LevelFormat.BULLET, text: '\u25A1',
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } }
        ]},
      ],
    },
    styles: {
      default: {
        document: { run: { font: 'Arial', size: 18 } },
      },
    },
    sections: [{
      properties: {
        page: {
          size: { width: PAGE_W, height: 16838 },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
        },
      },
      headers: { default: header },
      footers: { default: footer },
      children: [
        ...buildTitleBlock(data),
        ...buildContents(),
        ...buildSectionA(data.section_a),
        ...buildSectionB(data.section_b),
        ...buildSectionC(data.section_c),
        ...buildSectionD(data.section_d),
        ...buildSectionE(data.section_e),
      ],
    }],
  });

  return doc;
}

// ── Main ──────────────────────────────────────────────────────────────────────
(async () => {
  const inputFile = process.argv[2] || 'sample_data.json';
  let data;
  try {
    data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
  } catch (e) {
    console.error('Could not read input file:', inputFile);
    process.exit(1);
  }

  const doc    = await buildDocument(data);
  const buf    = await Packer.toBuffer(doc);
  const outPath = process.argv[3] || '/mnt/user-data/outputs/MASCI_Audit_Report.docx';
  fs.writeFileSync(outPath, buf);
  console.log('✓ Report generated:', outPath);
})();
