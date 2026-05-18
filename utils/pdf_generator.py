import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf_report(user_profile, sessions, roadmap_title="Combined"):
    """
    Generate a styled, premium PDF report for focus sessions and distraction telemetry.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Premium Harmonious Palette matching the App theme
    primary_color = colors.HexColor("#6366f1")   # Premium Purple
    dark_bg = colors.HexColor("#0f172a")          # Deep Slate
    text_color = colors.HexColor("#1e293b")       # Dark Text
    light_bg = colors.HexColor("#f8fafc")         # Soft White/Grey
    accent_green = colors.HexColor("#10b981")     # Green
    accent_red = colors.HexColor("#ef4444")       # Red
    accent_yellow = colors.HexColor("#f59e0b")    # Yellow
    
    # Custom Typography / Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=primary_color,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=dark_bg,
        spaceBefore=14,
        spaceAfter=6,
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        textColor=text_color,
        leading=13
    )
    
    kpi_val_style = ParagraphStyle(
        'KPIValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=primary_color,
        alignment=1 # Center
    )
    
    kpi_lbl_style = ParagraphStyle(
        'KPILabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor("#64748b"),
        alignment=1 # Center
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        textColor=colors.white,
        alignment=1
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=text_color,
        alignment=1
    )

    table_cell_left_style = ParagraphStyle(
        'TableCellLeft',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=text_color,
        alignment=0 # Left
    )
    
    story = []
    
    # ── HEADER BANNER ────────────────────────────────────────────────────────
    story.append(Paragraph("EDUAI PROGRESS TELEMETRY REPORT", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} · Focus Sessions & Distractions Logs", subtitle_style))
    
    # ── USER PROFILE SUMMARY ──────────────────────────────────────────────────
    user_name = user_profile.get('name', 'N/A') if user_profile else 'Guest Student'
    user_goal = user_profile.get('primary_goal', 'N/A') if user_profile else 'Combined Study Tracks'
    user_style = user_profile.get('learning_style', 'N/A') if user_profile else 'Not Configured'
    
    profile_data = [
        [Paragraph(f"<b>Student Name:</b> {user_name}", body_style), Paragraph(f"<b>Primary Goal:</b> {user_goal}", body_style)],
        [Paragraph(f"<b>Learning Style:</b> {user_style}", body_style), Paragraph(f"<b>Report Context:</b> {roadmap_title}", body_style)]
    ]
    
    profile_table = Table(profile_data, colWidths=[240, 280])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    
    story.append(profile_table)
    story.append(Spacer(1, 10))
    
    # Calculate statistics
    actual_durations = [float(s.get('actual_duration', 0)) for s in sessions]
    total_time_mins = sum(actual_durations)
    total_h = int(total_time_mins // 60)
    total_m = int(total_time_mins % 60)
    
    focus_scores = [float(s.get('focus_score', 0)) for s in sessions if s.get('focus_score') is not None]
    avg_focus = int(sum(focus_scores) / len(focus_scores)) if focus_scores else 0
    
    total_dist = sum(int(s.get('distraction_count', 0)) for s in sessions)
    phone_dist = sum(int(s.get('phone_count', 0)) for s in sessions)
    drowsy_dist = sum(int(s.get('drowsy_count', 0)) for s in sessions)
    zone_dist = sum(int(s.get('zone_out_count', 0)) for s in sessions)
    pauses_dist = sum(int(s.get('pause_count', 0)) for s in sessions)
    
    # ── KPI SUMMARY GRID ─────────────────────────────────────────────────────
    kpi_data = [
        [
            Paragraph("Flight Duration", kpi_lbl_style),
            Paragraph("Avg Focus Score", kpi_lbl_style),
            Paragraph("Logged Distractions", kpi_lbl_style),
            Paragraph("Total Sessions", kpi_lbl_style)
        ],
        [
            Paragraph(f"{total_h}h {total_m}m", kpi_val_style),
            Paragraph(f"{avg_focus}%", kpi_val_style),
            Paragraph(f"{total_dist}", kpi_val_style),
            Paragraph(f"{len(sessions)}", kpi_val_style)
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[130, 130, 130, 130])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor("#e2e8f0")),
        ('BOX', (0,0), (-1,-1), 1.2, primary_color),
    ]))
    
    story.append(Paragraph("Key Performance Indicators (KPIs)", h2_style))
    story.append(kpi_table)
    story.append(Spacer(1, 10))
    
    # ── DISTRACTION ANALYSIS ──────────────────────────────────────────────────
    dist_data = [
        [Paragraph("📱 Phone Distractions", body_style), Paragraph(f"<b>{phone_dist}</b> incidents logged", body_style)],
        [Paragraph("😴 Drowsiness Detections", body_style), Paragraph(f"<b>{drowsy_dist}</b> incidents logged", body_style)],
        [Paragraph("👁️ Zone-out Alerts", body_style), Paragraph(f"<b>{zone_dist}</b> incidents logged", body_style)],
        [Paragraph("⏸️ Study Pauses", body_style), Paragraph(f"<b>{pauses_dist}</b> pauses triggered", body_style)]
    ]
    dist_table = Table(dist_data, colWidths=[260, 260])
    dist_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('PADDING', (0,0), (-1,-1), 5),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor("#e2e8f0")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    
    story.append(Paragraph("Tracked Session Distractions Breakdown", h2_style))
    story.append(dist_table)
    story.append(Spacer(1, 10))
    
    # ── SESSION HISTORY LOG TABLE ───────────────────────────────────────────
    story.append(Paragraph("Telemetry Logs & Session Vault", h2_style))
    
    headers = [
        Paragraph("Date & Time", table_header_style),
        Paragraph("Duration", table_header_style),
        Paragraph("Focus Score", table_header_style),
        Paragraph("📱 Phone", table_header_style),
        Paragraph("😴 Drowsy", table_header_style),
        Paragraph("👁️ Zone", table_header_style),
        Paragraph("⏸️ Pauses", table_header_style)
    ]
    
    table_rows = [headers]
    
    for s in sessions:
        try:
            dt = datetime.strptime(s['start_time'], "%Y-%m-%d %H:%M:%S")
            d_str = dt.strftime("%b %d, %Y\n%I:%M %p")
        except:
            d_str = s.get('start_time', 'Unknown')
            
        score = int(s.get('focus_score', 0))
        mins = f"{round(float(s.get('actual_duration', 0)), 1)}m"
        phone = str(s.get('phone_count', 0))
        drowsy = str(s.get('drowsy_count', 0))
        zone = str(s.get('zone_out_count', 0))
        pause = str(s.get('pause_count', 0))
        
        # Color coding for scores
        score_text = f"<b>{score}%</b>"
        if score >= 80:
            score_color = accent_green
        elif score >= 60:
            score_color = accent_yellow
        else:
            score_color = accent_red
            
        score_style = ParagraphStyle(
            f"ScoreStyle_{s['id']}",
            parent=table_cell_style,
            fontName='Helvetica-Bold',
            textColor=score_color
        )
        
        table_rows.append([
            Paragraph(d_str.replace('\n', '<br/>'), table_cell_left_style),
            Paragraph(mins, table_cell_style),
            Paragraph(score_text, score_style),
            Paragraph(phone if phone != '0' else '-', table_cell_style),
            Paragraph(drowsy if drowsy != '0' else '-', table_cell_style),
            Paragraph(zone if zone != '0' else '-', table_cell_style),
            Paragraph(pause if pause != '0' else '-', table_cell_style)
        ])
        
    session_table = Table(table_rows, colWidths=[110, 60, 80, 65, 65, 65, 75])
    session_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg])
    ]))
    
    story.append(session_table)
    
    # ── AI RECOMMENDATIONS SECTION ──────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(KeepTogether([
        Paragraph("Actionable Recommendations for Focus Excellence", h2_style),
        Paragraph(
            "1. <b>Curb Phone Distractions:</b> If your phone counts are high, enable Focus Mode/Do Not Disturb on your phone. Put it out of arm's reach or in another room to break the unconscious checking cycle.<br/>"
            "2. <b>Mitigate Fatigue & Drowsiness:</b> High drowsiness alerts imply sleep deficit or studying at low-energy hours. Ensure adequate hydration, stand up/stretch every 20-30 mins, and keep your study environment well-lit.<br/>"
            "3. <b>Prevent Mind Wandering (Zone-outs):</b> Zone-out triggers can be combatted by breaking study chapters into highly specific, byte-sized goals with active note-taking rather than passive reading.",
            body_style
        )
    ]))
    
    doc.build(story)
    buffer.seek(0)
    return buffer
