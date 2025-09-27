import json
import re
from typing import Dict, List, Any
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict
from pydantic.fields import PrivateAttr
from dataclasses import dataclass

@dataclass
class CameraConfig:
    motion: str = "smooth tracking shot"
    angle: str = "eye-level"
    lens_type: str = "50mm"
    framing: str = "medium shot"
    movement: str = "static"

@dataclass
class LightingConfig:
    mood: str = "soft daylight"
    time_of_day: str = "late afternoon"
    style: str = "natural lighting"
    atmosphere: str = "warm and inviting"

@dataclass
class AudioConfig:
    dialogue: List[str] = None
    ambient_sounds: List[str] = None
    music: str = ""
    voice_style: str = "natural, conversational"

class VEO3PromptStructure(BaseModel):
    prompt: str = Field(description="Main text description of the video")
    negative_prompt: str = Field(default="", description="Elements to avoid or exclude")
    config: Dict[str, Any] = Field(description="Advanced VEO3 configuration")
    character_bible: Dict[str, str] = Field(default_factory=dict, description="Character consistency data")
    scene_context: Dict[str, Any] = Field(default_factory=dict, description="Scene-specific information")

class VEO3PromptTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "VEO3 Video Prompt Generator"
    description: str = """
    Advanced prompt generation tool specifically designed for Google VEO3 AI video generation.
    Creates optimized JSON prompts with character consistency, period authenticity, and 
    sophisticated audio-visual control.
    """

    # Private runtime state
    _character_bible: Dict[str, str] = PrivateAttr(default_factory=dict)
    _scene_counter: int = PrivateAttr(default=0)
    _camera_presets: Dict[str, CameraConfig] = PrivateAttr()
    _period_styles: Dict[str, Dict[str, Any]] = PrivateAttr()
    _audio_templates: Dict[str, Dict[str, Any]] = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._character_bible = {}
        self._scene_counter = 0
        self._camera_presets = self._initialize_camera_presets()
        self._period_styles = self._initialize_period_styles()
        self._audio_templates = self._initialize_audio_templates()

    # Optional properties to keep call sites tidy
    @property
    def character_bible(self) -> Dict[str, str]:
        return self._character_bible

    @property
    def camera_presets(self) -> Dict[str, CameraConfig]:
        return self._camera_presets

    @property
    def period_styles(self) -> Dict[str, Dict[str, Any]]:
        return self._period_styles

    @property
    def audio_templates(self) -> Dict[str, Dict[str, Any]]:
        return self._audio_templates

    def _run(
        self,
        script_segment: str,
        character_descriptions: Dict[str, str] = None,
        scene_type: str = "general",
        duration: int = 8,
        visual_style: str = "cinematic",
        period_setting: str = "",
        audio_requirements: List[str] = None,
        technical_specs: Dict[str, Any] = None,
    ) -> str:
        try:
            if character_descriptions:
                self._character_bible.update(character_descriptions)

            prompt_structure = self._generate_prompt_structure(
                script_segment=script_segment,
                scene_type=scene_type,
                duration=duration,
                visual_style=visual_style,
                period_setting=period_setting,
                audio_requirements=audio_requirements or [],
                technical_specs=technical_specs or {},
            )

            veo3_prompt = self._format_for_veo3(prompt_structure)
            variations = self._generate_prompt_variations(prompt_structure, 3)
            return self._format_output(veo3_prompt, variations, prompt_structure)
        except Exception as e:
            return f"❌ Error generating VEO3 prompt: {str(e)}"

    def _initialize_camera_presets(self) -> Dict[str, CameraConfig]:
        return {
            "establishing": CameraConfig("slow crane down", "aerial", "24mm", "wide shot", "crane movement"),
            "dialogue": CameraConfig("subtle handheld breathing", "eye-level", "85mm", "medium close-up", "static"),
            "action": CameraConfig("dynamic tracking", "low angle", "35mm", "medium shot", "following action"),
            "intimate": CameraConfig("smooth dolly-in", "slightly low", "50mm", "close-up", "slow dolly"),
            "dramatic": CameraConfig("rack focus pull", "dutch angle", "135mm", "tight close-up", "focus pull"),
            "epic": CameraConfig("sweeping crane shot", "high angle", "16mm", "extreme wide", "circular crane"),
        }

    def _initialize_period_styles(self) -> Dict[str, Dict[str, Any]]:
        return {
            "korean_historical": {
                "costume_details": "authentic hanbok with jade accessories, gat hat",
                "environment": "traditional Korean architecture, hanji windows, wooden floors",
                "color_grading": "warm earth tones, soft contrast, muted palette",
                "props": "calligraphy scrolls, ceramic tea sets, bronze incense burners",
                "architecture": "curved roof tiles, wooden pillars, stone courtyards",
            },
            "medieval": {
                "costume_details": "period-accurate tunics, cloaks, leather boots",
                "environment": "stone castles, wooden taverns, cobblestone streets",
                "color_grading": "desaturated with warm firelight accents",
                "props": "swords, shields, scrolls, candles",
                "architecture": "gothic arches, stone walls, heavy wooden doors",
            },
            "victorian": {
                "costume_details": "formal dress coats, corsets, top hats, gloves",
                "environment": "gaslit streets, ornate parlors, grand staircases",
                "color_grading": "sepia tones with golden highlights",
                "props": "pocket watches, letters, oil lamps, carriages",
                "architecture": "detailed moldings, tall windows, brick facades",
            },
        }

    def _initialize_audio_templates(self) -> Dict[str, Dict[str, Any]]:
        return {
            "dialogue_scene": {
                "structure": "Character speaks: '[dialogue]' with [emotion] delivery",
                "ambient": ["soft background atmosphere", "subtle environmental sounds"],
                "mixing": "dialogue prioritized, ambient at 30% volume",
            },
            "action_scene": {
                "structure": "Dynamic action sounds with movement audio",
                "ambient": ["impact sounds", "movement foley", "environmental reactions"],
                "mixing": "high energy sound design, layered audio",
            },
            "establishing_scene": {
                "structure": "Rich atmospheric audio establishing location",
                "ambient": ["environmental sounds", "distant activity", "weather elements"],
                "mixing": "wide stereo field, immersive soundscape",
            },
        }

    def _generate_prompt_structure(
        self,
        script_segment: str,
        scene_type: str,
        duration: int,
        visual_style: str,
        period_setting: str,
        audio_requirements: List[str],
        technical_specs: Dict[str, Any],
    ) -> VEO3PromptStructure:
        self._scene_counter += 1

        dialogue = self._extract_dialogue(script_segment)
        actions = self._extract_actions(script_segment)
        characters_mentioned = self._identify_characters(script_segment)

        main_prompt = self._build_main_prompt(
            script_segment, characters_mentioned, actions, dialogue, period_setting, visual_style
        )
        negative_prompt = self._generate_negative_prompt(period_setting)
        config = self._build_config(
            duration, scene_type, visual_style, period_setting, audio_requirements, technical_specs, dialogue
        )
        scene_context = {
            "scene_number": self._scene_counter,
            "script_segment": script_segment,
            "key_characters": characters_mentioned,
            "scene_type": scene_type,
            "visual_style": visual_style,
        }

        return VEO3PromptStructure(
            prompt=main_prompt,
            negative_prompt=negative_prompt,
            config=config,
            character_bible=self._character_bible,
            scene_context=scene_context,
        )

    def _extract_dialogue(self, script_segment: str) -> List[str]:
        patterns = [
            r'"([^"]*)"',
            r"'([^']*)'",
            r'says?:\s*"([^"]*)"',
            r'whispers?:\s*"([^"]*)"',
        ]
        dialogues: List[str] = []
        for p in patterns:
            dialogues.extend(re.findall(p, script_segment, re.IGNORECASE))
        return list(set(dialogues))

    def _extract_actions(self, script_segment: str) -> List[str]:
        action_words = [
            "walks","runs","turns","looks","reaches","grabs","opens","closes","sits",
            "stands","kneels","bows","nods","smiles","frowns","enters","exits","approaches","retreats",
        ]
        actions: List[str] = []
        for sentence in re.split(r"[.!?]+", script_segment):
            if any(w in sentence.lower() for w in action_words):
                actions.append(sentence.strip())
        return actions

    def _identify_characters(self, script_segment: str) -> List[str]:
        mentioned = []
        for name in self._character_bible.keys():
            if name.lower() in script_segment.lower():
                mentioned.append(name)
        return mentioned

    def _build_main_prompt(
        self,
        script_segment: str,
        characters: List[str],
        actions: List[str],
        dialogue: List[str],
        period_setting: str,
        visual_style: str,
    ) -> str:
        parts: List[str] = []
        for name in characters:
            if name in self._character_bible:
                parts.append(self._character_bible[name])

        if period_setting and period_setting in self._period_styles:
            style = self._period_styles[period_setting]
            parts.append(f"Period setting: {period_setting}")
            parts.append(style.get("costume_details", ""))
            parts.append(style.get("environment", ""))

        parts.append(". ".join(actions) if actions else script_segment)

        for line in dialogue:
            if line.strip():
                parts.append(f'Character says: "{line}" with natural delivery')

        parts.append(f"Visual style: {visual_style}, photorealistic")
        return ". ".join([p for p in parts if p.strip()])

    def _generate_negative_prompt(self, period_setting: str) -> str:
        base = [
            "blurry", "low quality", "distorted faces", "extra limbs",
            "watermarks", "text overlays", "modern elements", "anachronistic details",
        ]
        period_neg = {
            "korean_historical": ["western clothing", "modern buildings", "cars", "phones"],
            "medieval": ["modern clothing", "electricity", "contemporary items"],
            "victorian": ["casual modern wear", "contemporary technology"],
        }
        negatives = base[:]
        if period_setting in period_neg:
            negatives.extend(period_neg[period_setting])
        return ", ".join(negatives)

    def _build_config(
        self,
        duration: int,
        scene_type: str,
        visual_style: str,
        period_setting: str,
        audio_requirements: List[str],
        technical_specs: Dict[str, Any],
        dialogue: List[str],
    ) -> Dict[str, Any]:
        camera = self._camera_presets.get(scene_type, self._camera_presets["dialogue"])
        config: Dict[str, Any] = {
            "duration_seconds": min(duration, 8),
            "aspect_ratio": "16:9",
            "generate_audio": True,
            "resolution": "1080p",
            "camera": {
                "motion": camera.motion,
                "angle": camera.angle,
                "lens_type": camera.lens_type,
                "framing": camera.framing,
                "movement": camera.movement,
            },
            "lighting": {
                "mood": "cinematic lighting",
                "time_of_day": technical_specs.get("time_of_day", "day"),
                "style": "professional film lighting",
            },
            "audio": {
                "dialogue": dialogue,
                "ambient": audio_requirements,
                "style": "professional film audio",
            },
            "style": f"{visual_style}, high production value",
        }
        if period_setting and period_setting in self._period_styles:
            style = self._period_styles[period_setting]
            config["period"] = period_setting
            config["color_grading"] = style.get("color_grading", "natural")
        if technical_specs:
            # shallow merge for top-level, with nested camera/lighting merges if provided
            for k, v in technical_specs.items():
                if isinstance(v, dict) and k in ("camera", "lighting", "audio"):
                    config.setdefault(k, {}).update(v)
                else:
                    config[k] = v
        return config

    def _format_for_veo3(self, s: VEO3PromptStructure) -> Dict[str, Any]:
        return {
            "instances": [{
                "prompt": s.prompt,
                "negativePrompt": s.negative_prompt,
                "aspectRatio": s.config.get("aspect_ratio", "16:9"),
                "resolution": s.config.get("resolution", "1080p"),
                "generateAudio": True,
                "personGeneration": "allow_adult",
            }],
            "parameters": {"seed": None, "generateAudio": True},
            "advanced_config": s.config,
        }

    def _generate_prompt_variations(self, base: VEO3PromptStructure, count: int) -> List[Dict[str, Any]]:
        variations: List[Dict[str, Any]] = []
        strategies = ["camera_angle_variation", "lighting_variation", "pacing_variation"]
        for i in range(min(count, len(strategies))):
            v = base.model_copy(deep=True)
            strat = strategies[i]
            if strat == "camera_angle_variation":
                v.config.setdefault("camera", {})["angle"] = "slightly high angle"
                v.prompt += ". Camera positioned slightly above eye level."
            elif strat == "lighting_variation":
                v.config.setdefault("lighting", {})["mood"] = "dramatic chiaroscuro"
                v.prompt += ". Strong contrast lighting with deep shadows."
            elif strat == "pacing_variation":
                v.config.setdefault("camera", {})["motion"] = "slow motion emphasis"
                v.prompt += ". Slow, deliberate pacing for dramatic effect."
            variations.append(self._format_for_veo3(v))
        return variations

    def _format_output(self, main_prompt: Dict[str, Any], variations: List[Dict[str, Any]], s: VEO3PromptStructure) -> str:
        def fmt_characters() -> str:
            if not self._character_bible:
                return "• No character descriptions provided"
            return "\n".join([f"• {n}: {d[:80]}..." for n, d in self._character_bible.items()])

        def fmt_variations() -> str:
            if not variations:
                return "• No variations generated"
            lines = []
            for i, v in enumerate(variations, 1):
                lines.append(f"• Variation {i}: Modified {list(v.get('advanced_config', {}).keys())}")
            return "\n".join(lines)

        def fmt_audio(a: Dict[str, Any]) -> str:
            if not a:
                return "• Standard ambient audio generation"
            out = []
            if a.get("dialogue"):
                out.append(f"• Dialogue: {len(a['dialogue'])} lines")
            if a.get("ambient"):
                out.append(f"• Ambient: {', '.join(a['ambient'])}")
            if a.get("style"):
                out.append(f"• Style: {a['style']}")
            return "\n".join(out) if out else "• Standard audio generation"

        output = f"""
=== VEO3 OPTIMIZED VIDEO GENERATION PROMPTS ===

🎬 SCENE {s.scene_context.get('scene_number', 1)} - {s.scene_context.get('scene_type', 'General').upper()}

📝 PRIMARY PROMPT (RECOMMENDED):

🎯 KEY OPTIMIZATION FEATURES:
• Character Consistency: {"✅ Applied" if s.character_bible else "❌ No character data"}
• Period Authenticity: {"✅ Applied" if any("period" in k for k in s.config.keys()) else "❌ Modern setting"}
• Audio Integration: ✅ Native VEO3 audio generation enabled
• Camera Work: ✅ Professional cinematography settings
• Duration Optimized: {s.config.get('duration_seconds', 8)} seconds (VEO3 optimal)

📋 SCENE BREAKDOWN:
Script Segment: {s.scene_context.get('script_segment', 'N/A')[:100]}...
Visual Style: {s.scene_context.get('visual_style', 'N/A')}
Key Characters: {', '.join(s.scene_context.get('key_characters', []))}

🎭 CHARACTER BIBLE APPLIED:
{fmt_characters()}

🔄 ALTERNATIVE VARIATIONS:
{fmt_variations()}

⚙️ TECHNICAL SPECIFICATIONS:
• Resolution: {main_prompt['instances'][0].get('resolution', '1080p')}
• Aspect Ratio: {main_prompt['instances'][0].get('aspectRatio', '16:9')}
• Audio Generation: {main_prompt['instances'][0].get('generateAudio', True)}
• Person Generation: {main_prompt['instances'][0].get('personGeneration', 'allow_adult')}

🎵 AUDIO ELEMENTS:
{fmt_audio(s.config.get('audio', {}))}

🚀 READY FOR VEO3 GENERATION
Copy the primary prompt JSON directly into your VEO3 interface or API call.
""".strip()
        return output

# Factory
def create_veo3_prompt_tool():
    return VEO3PromptTool()
