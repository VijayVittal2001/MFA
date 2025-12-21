# cli/session.py
# FINAL — 100% CROSS-PLATFORM (Windows / Linux / macOS / Docker / Render)

import typer
import cv2
import numpy as np
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich import box
from datetime import datetime, timezone
import time

from utils.keyboard import get_key

from services.embedding import get_face_embedding
from services.comparison import verify_match
from services.voice_embedding import verify_voice_live
from services.face_detection import get_cropped_face
from db.session_repo import mark_session

console = Console()

CONFIG = {
    "face_threshold": 0.60,
    "voice_threshold": 0.62,
    "max_attempts": 300,
    "frame_skip": 2,
    "delay_between_sessions": 2.0
}


class BiometricSession:
    def __init__(self):
        self.console = console

    # ================= VOICE + SESSION =================
    def _voice_verification_and_mark(self, user):
        name = user["name"]
        email = user["email"]
        conf = user["confidence"]

        console.print(f"\n[bold green]Hello {name} — Face verified ({conf:.1%})[/bold green]")
        console.print("[bold cyan]Press V to verify voice • N to skip • (Auto-skip in 10s)[/bold cyan]")
        console.print("[bold]V/N: [/bold]", end="")

        choice = None
        start_time = time.time()

        while time.time() - start_time < 10.0:
            key = get_key().lower()

            if key == "v":
                choice = "v"
                console.print("V")
                break
            elif key == "n":
                choice = "n"
                console.print("N")
                break

            time.sleep(0.1)

        # ---- AUTO SKIP ----
        if choice is None:
            console.print("\n[bold yellow]10 seconds passed — Auto skipping voice...[/bold yellow]")
            time.sleep(1.5)
            return

        if choice == "n":
            console.print("[yellow]Voice verification skipped[/yellow]")
            time.sleep(1.5)
            return

        # ---- VOICE VERIFY ----
        try:
            stored_voice = np.array(user["voice_embedding"])
        except Exception:
            console.print("[red]No voice embedding found[/red]")
            time.sleep(2)
            return

        console.print("\n[bold blue]Speak now for 7 seconds...[/bold blue]")

        try:
            voice_score, passed = verify_voice_live(
                stored_voice,
                duration=7.0,
                threshold=CONFIG["voice_threshold"]
            )
        except Exception as e:
            console.print(f"[red]Voice recording failed: {e}[/red]")
            time.sleep(2)
            return

        if not passed:
            console.print(f"\n[bold red]VOICE FAILED ({voice_score:.1%}) — ACCESS DENIED[/bold red]")
            self._print_time()
            time.sleep(3)
            return

        console.print(f"[bold green]VOICE VERIFIED! ({voice_score:.1%})[/bold green]")

        action, message = mark_session(user["user_id"], name, email)
        self._show_result(action, name, email, conf, voice_score, message)
        self._print_time()

        console.print("\n[bold magenta]Session complete — Ready for next user...[/bold magenta]\n")
        time.sleep(CONFIG["delay_between_sessions"])

    # ================= FACE SESSION =================
    def run_single_session(self):
        console.print("\n[bold blue]Scanning for next user...[/bold blue]")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            console.print("[bold red]ERROR: Cannot open webcam[/bold red]")
            return False

        live = Live(
            Panel("Look at camera...", border_style="bright_blue", box=box.ROUNDED),
            refresh_per_second=4,
            console=console
        )
        live.start()

        face_matched = False
        user_data = None

        try:
            frame_count = 0
            while frame_count < CONFIG["max_attempts"]:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                if frame_count % CONFIG["frame_skip"] != 0:
                    continue

                cropped = get_cropped_face(frame)
                if cropped is None:
                    live.update(Panel("Waiting for face...", border_style="dim white", box=box.ROUNDED))
                    cv2.imshow("Biometric Kiosk", frame)
                    if cv2.waitKey(1) == 27:
                        raise KeyboardInterrupt
                    continue

                embedding = get_face_embedding(cropped)
                if embedding is None:
                    continue

                result = verify_match(embedding, threshold=CONFIG["face_threshold"])

                if result.get("matched"):
                    user_data = result
                    name = user_data["name"]
                    email = user_data["email"]
                    conf = user_data["confidence"]

                    status = Text("FACE RECOGNIZED!\n", style="bold green")
                    status.append(f"{name}\n", style="bold yellow")
                    status.append(f"{email}\n", style="cyan")
                    status.append(f"Confidence: {conf:.1%}", style="bright_white")

                    live.update(Panel(status, border_style="green", box=box.DOUBLE))
                    face_matched = True
                    break
                else:
                    best = result.get("confidence", 0)
                    msg = f"Unknown ({best:.1%})" if best > 0.3 else "Please step forward"
                    live.update(Panel(msg, border_style="red"))

                cv2.imshow("Biometric Kiosk", frame)
                if cv2.waitKey(1) == 27:
                    raise KeyboardInterrupt

        finally:
            cap.release()
            cv2.destroyAllWindows()
            live.stop()

        if face_matched and user_data:
            self._voice_verification_and_mark(user_data)
            return True

        time.sleep(1)
        return False

    # ================= UI HELPERS =================
    def _show_result(self, action, name, email, face_conf, voice_conf, msg):
        if action == "LOGIN":
            console.print("\n[bold green]LOGIN SUCCESSFUL![/bold green]")
        elif action == "LOGOUT":
            console.print("\n[bold magenta]LOGOUT SUCCESSFUL![/bold magenta]")
        else:
            console.print(f"\n[bold red]{action.replace('_', ' ').title()}[/bold red]")

        console.print(f"User: [bold yellow]{name}[/bold yellow] ({email})")
        console.print(f"Face: {face_conf:.1%} | Voice: {voice_conf:.1%}")
        console.print(f"[dim]{msg}[/dim]")

    def _print_time(self):
        now = datetime.now(timezone.utc).strftime("%H:%M:%S • %d %b %Y UTC")
        console.print(f"[dim]{now}[/dim]")


# ================= ENTRY =================
def session():
    console.print("[bold magenta]BIOMETRIC KIOSK STARTED — 10s AUTO-SKIP ENABLED[/bold magenta]")
    console.print("[bold green]Face → optional voice → auto next user[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    kiosk = BiometricSession()

    while True:
        try:
            kiosk.run_single_session()
        except KeyboardInterrupt:
            console.print("\n[bold red]Stopped by admin[/bold red]")
            break
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            time.sleep(2)


if __name__ == "__main__":
    typer.run(session)
