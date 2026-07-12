"""BounceGen Maya - Ball Types & Physical Properties"""
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass(frozen=True)
class BallProperties:
    cor: float                      # coefficient of restitution (bounciness)
    default_squash: float           # 0 = perfectly rigid, no squash
    default_stretch: float          # 0 = perfectly rigid, no stretch
    density: float
    default_radius: float
    default_color: Tuple[float, float, float]

# COR values are tuned for believable on-screen behavior (matching how a
# viewer expects each ball to feel), not for lab-precise coefficients -
# e.g. a steel ball bearing CAN be extremely bouncy on a steel plate in
# real life, but on an ordinary floor (and in viewer expectation) a heavy
# metal ball should read as a dull, low thud, not the bounciest ball in
# the scene.
BALL_TYPE_DATA: Dict[str, BallProperties] = {
    "Ping Pong":    BallProperties(cor=0.88, default_squash=0.55, default_stretch=1.35, density=0.2, default_radius=0.18, default_color=(0.98, 0.97, 0.92)),
    "Tennis":       BallProperties(cor=0.72, default_squash=0.50, default_stretch=1.45, density=0.5, default_radius=0.33, default_color=(0.80, 0.95, 0.15)),
    "Golf":         BallProperties(cor=0.78, default_squash=0.15, default_stretch=1.10, density=1.2, default_radius=0.22, default_color=(0.96, 0.96, 0.94)),
    "Basketball":   BallProperties(cor=0.75, default_squash=0.50, default_stretch=1.40, density=0.8, default_radius=1.20, default_color=(0.85, 0.45, 0.12)),
    "Baseball":     BallProperties(cor=0.40, default_squash=0.15, default_stretch=1.10, density=1.0, default_radius=0.37, default_color=(0.94, 0.92, 0.85)),
    "Bowling":      BallProperties(cor=0.35, default_squash=0.08, default_stretch=1.05, density=3.0, default_radius=1.10, default_color=(0.06, 0.06, 0.09)),
    "Hockey Puck":  BallProperties(cor=0.15, default_squash=0.05, default_stretch=1.02, density=2.5, default_radius=0.40, default_color=(0.02, 0.02, 0.02)),
    "Steel Ball":   BallProperties(cor=0.40, default_squash=0.02, default_stretch=1.01, density=5.0, default_radius=0.35, default_color=(0.72, 0.73, 0.76)),
    "Glass Marble": BallProperties(cor=0.55, default_squash=0.03, default_stretch=1.02, density=2.0, default_radius=0.15, default_color=(0.65, 0.85, 0.92)),
    "Custom":       BallProperties(cor=0.50, default_squash=0.40, default_stretch=1.30, density=1.0, default_radius=1.00, default_color=(0.80, 0.30, 0.10)),
}

def get_ball_properties(type_name: str) -> BallProperties:
    return BALL_TYPE_DATA.get(type_name, BALL_TYPE_DATA["Custom"])
