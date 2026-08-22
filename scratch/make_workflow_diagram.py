import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
from pathlib import Path

def generate_improved_diagram():
    # Set high DPI figure
    fig, ax = plt.subplots(figsize=(15, 8), dpi=300)
    
    # Background color
    bg_color = '#0B0F19'
    ax.set_facecolor(bg_color)
    fig.patch.set_facecolor(bg_color)
    ax.axis('off')
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 8)

    # Color Palette
    CYAN = '#00F2FE'
    TEAL = '#4BC6B9'
    CORAL = '#FF7E5F'
    GOLD = '#FFB703'
    PURPLE = '#9D4EDD'
    BLUE = '#3B82F6'
    CARD_BG = '#131D2E'
    TEXT_MUTED = '#94A3B8'
    TEXT_BRIGHT = '#F8FAFC'

    # Title Banner
    plt.title("VoxLoop — End-to-End Multi-Agent Voice Feedback Architecture", 
              color=TEXT_BRIGHT, fontsize=16, pad=20, weight='bold', fontfamily='sans-serif')

    # Helper function for stage container cards
    def draw_stage(x, y, w, h, step_num, title, border_color):
        # Stage Outer Container
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12", 
                                      facecolor='#0F172A', edgecolor=border_color, linewidth=2.0, alpha=0.95)
        ax.add_patch(rect)
        
        # Step Header Badge
        badge = patches.FancyBboxPatch((x + 0.15, y + h - 0.55), 0.95, 0.38, boxstyle="round,pad=0.06",
                                       facecolor=border_color, edgecolor='none')
        ax.add_patch(badge)
        ax.text(x + 0.62, y + h - 0.36, f"STEP {step_num}", color='#080C14', weight='bold', fontsize=8.5, ha='center', va='center')
        
        # Stage Title
        ax.text(x + 1.22, y + h - 0.36, title, color=TEXT_BRIGHT, weight='bold', fontsize=10.5, ha='left', va='center')

    # Helper function for internal node boxes
    def draw_node(x, y, w, h, icon_title, subtitle, accent_color):
        node = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", 
                                       facecolor=CARD_BG, edgecolor=accent_color, linewidth=1.4)
        ax.add_patch(node)
        ax.text(x + w/2, y + h*0.62, icon_title, color=TEXT_BRIGHT, weight='bold', fontsize=9.5, ha='center', va='center')
        ax.text(x + w/2, y + h*0.28, subtitle, color=TEXT_MUTED, fontsize=8, ha='center', va='center')

    # Helper function for connectors
    def draw_link(x1, y1, x2, y2, label="", color=CYAN, connectionstyle="arc3,rad=0"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.0, 
                                    mutation_scale=16, connectionstyle=connectionstyle))
        if label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            t = ax.text(mid_x, mid_y + 0.18, label, color=color, fontsize=8, 
                        weight='bold', ha='center', va='center')
            t.set_path_effects([path_effects.withStroke(linewidth=3, foreground=bg_color)])

    # Draw 4 Main Stage Containers (Clean bounds)
    draw_stage(0.3, 0.8, 3.3, 6.2, "1", "Client Interface", CYAN)
    draw_stage(3.9, 0.8, 3.4, 6.2, "2", "Audio Engine", TEAL)
    draw_stage(7.6, 0.8, 3.6, 6.2, "3", "LangGraph Loop", CORAL)
    draw_stage(11.5, 0.8, 3.1, 6.2, "4", "AI & Storage", PURPLE)


    # --- STAGE 1 NODES (Client) ---
    draw_node(0.7, 5.0, 2.6, 1.1, "User Microphone", "MediaRecorder WebM Stream", CYAN)
    draw_node(0.7, 3.1, 2.6, 1.1, "Right Chat Panel", "Multi-Turn History Bubbles", CYAN)
    draw_node(0.7, 1.2, 2.6, 1.1, "Scorecard Gauges", "6 Evaluation Metric Bars", GOLD)

    # --- STAGE 2 NODES (Speech & Storage) ---
    draw_node(4.3, 5.0, 2.6, 1.1, "WebSocket Handler", "FastAPI /ws/voice-turn", TEAL)
    draw_node(4.3, 3.1, 2.6, 1.1, "Faster-Whisper (STT)", "Local CPU / VAD Filter", TEAL)
    draw_node(4.3, 1.2, 2.6, 1.1, "pyttsx3 (TTS Engine)", "Offline .WAV Synthesis", TEAL)

    # --- STAGE 3 NODES (LangGraph Multi-Agent Loop) ---
    draw_node(7.9, 5.0, 3.0, 1.1, "1. Draft Response Agent", "Persona & Context Prompt", CORAL)
    draw_node(7.9, 3.1, 3.0, 1.1, "2. Critic Review Agent", "6 Metric Scorecard Evaluation", GOLD)
    draw_node(7.9, 1.2, 3.0, 1.1, "3. Improved Synthesis", "Refined Voice Phrasing", CORAL)

    # --- STAGE 4 NODES (AI & Storage) ---
    draw_node(11.9, 4.2, 2.4, 1.3, "Mistral AI API", "mistral-small-latest", PURPLE)
    draw_node(11.9, 1.2, 2.4, 1.3, "SQLite Database", "voxloop.db Storage", BLUE)

    # --- CONNECTING ARROWS ---
    # Client Mic -> WS Handler
    draw_link(3.3, 5.55, 4.3, 5.55, "WebM Bytes", CYAN)
    
    # WS Handler -> Faster-Whisper STT
    draw_link(5.6, 5.0, 5.6, 4.2, "")
    
    # Faster-Whisper -> Draft Agent
    draw_link(6.9, 3.65, 7.9, 5.55, "Transcript Text", TEAL, "arc3,rad=-0.12")
    
    # Draft -> Critic Agent
    draw_link(9.4, 5.0, 9.4, 4.2, "Draft Text", CORAL)
    
    # Critic Agent -> Mistral AI (JSON Schema)
    draw_link(10.9, 3.65, 11.9, 4.85, "Grading Schema", PURPLE, "arc3,rad=-0.1")
    
    # Critic -> Improve Agent
    draw_link(9.4, 3.1, 9.4, 2.3, "Critique & Scores", GOLD)
    
    # Improve Agent -> Mistral AI
    draw_link(10.9, 1.75, 11.9, 4.45, "Rewrite Request", PURPLE, "arc3,rad=-0.15")
    
    # Improve Agent -> TTS Engine
    draw_link(7.9, 1.75, 6.9, 1.75, "Improved Text", TEAL)
    
    # Improve Agent -> SQLite Database
    draw_link(10.9, 1.55, 11.9, 1.55, "Save Run Memory", BLUE)

    # WS Handler -> Client Scorecard & Chat
    draw_link(4.3, 5.35, 3.3, 3.65, "Payload Event", CYAN, "arc3,rad=0.15")
    draw_link(4.3, 5.35, 3.3, 1.75, "Scores & Metrics", GOLD, "arc3,rad=0.2")

    # Footer note
    ax.text(7.5, 0.3, "VoxLoop Multi-Agent Architecture • Built with FastAPI, LangGraph, Mistral AI & Faster-Whisper", 
            color=TEXT_MUTED, fontsize=9, ha='center', va='center', style='italic')

    # Save output image
    output_path = Path("scratch/voxloop_workflow_diagram.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
    plt.close()
    print(f"High-resolution diagram successfully generated at: {output_path.resolve()}")

if __name__ == "__main__":
    generate_improved_diagram()
