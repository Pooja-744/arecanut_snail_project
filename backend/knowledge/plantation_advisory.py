"""
Agricultural Advisory Knowledge Base for Arecanut Plantations & Giant African Snail.
Provides structured knowledge for chatbot context grounding and agronomic advisory.
"""

KNOWLEDGE_DATA = {
    "plantation_overview": {
        "crop": "Arecanut (Areca catechu L.)",
        "major_regions": ["Karnataka (Malnad, Coastal)", "Kerala", "Assam", "Meghalaya", "Tamil Nadu", "West Bengal"],
        "ideal_climate": "Tropical humid, 14-36°C, annual rainfall 1500-4000 mm, well-drained laterite or red loam soil.",
    },
    "pest": {
        "name": "Giant African Snail (Lissachatina fulica)",
        "type": "Invasive Mollusc",
        "active_period": "Nocturnal (active post-dusk, dawn, and overcast rainy days)",
        "damage_profile": {
            "low_damage": "Superficial scraping on lower fronds and stems. Isolated individuals (1-2 snails).",
            "moderate_damage": "Pronounced leaf holes, nibbled tender shoots, aggregation of 3-5 snails around tree base.",
            "severe_damage": "Heavy defoliation, chewed seedling whorls, bark rasping, dense clusters (>5 snails) threatening plant survival."
        },
        "control_measures": {
            "physical": [
                "Hand-collection wearing rubber gloves during early dawn (5:30 AM - 7:00 AM) or after rain.",
                "Euthanize collected snails by dropping into 10-15% common salt (NaCl) solution or boiling water.",
                "Create a 15-20 cm barrier ring of dry slaked lime, copper sulphate, or wood ash around tree trunks.",
                "Wrap copper tape around valuable sapling collars (copper creates a natural galvanic barrier snails will not cross)."
            ],
            "chemical_and_baiting": [
                "Iron (III) Phosphate 1% pellets (Eco-safe, pet & earthworm friendly, degrades into soil nutrients) spread around palm base.",
                "Metaldehyde 2.5% or 5% pellets applied under shaded damp tiles/banana leaf shelters (toxic to domestic animals; handle with care).",
                "Wet bait traps: 100g jaggery/molasses + 5g baker's yeast + fermented papaya/banana mash in earthen pots buried at ground level."
            ],
            "cultural": [
                "Eliminate weed growth, rotten logs, discarded plastic sacks, and coconut husks where snails aestivate during dry hours.",
                "Maintain clear inter-row drainage channels to prevent prolonged puddling."
            ]
        }
    },
    "diseases": {
        "KOLEROGA": {
            "common_name": "Koleroga / Mahali / Fruit Rot",
            "causative_agent": "Phytophthora meadii (Oomycete fungus)",
            "season": "Peak South-West Monsoon (June to September)",
            "symptoms": "Water-soaked dark lesions on developing arecanuts, nut dropping (Mahali shed), rotting of fruit bunches with white felt-like mycelium.",
            "management": [
                "Prophylactic pre-monsoon spraying of 1% Bordeaux mixture (1 kg copper sulphate + 1 kg lime + 100 L water) to entire fruit bunches.",
                "Repeat second spray 40-45 days after the first spray during mid-monsoon dry breaks.",
                "Polythene bunch covering (100 gauge translucent UV-resistant sheets) before monsoon rain begins.",
                "Collect and burn or deeply bury all fallen infected nuts to break fungal inoculum cycle."
            ]
        },
        "BUD_ROT": {
            "common_name": "Bud Rot (Kole Roga)",
            "causative_agent": "Phytophthora meadii / palmivora",
            "season": "Monsoon rainy period",
            "symptoms": "Spindle leaf turns yellow and droops, crown central whorl decays emitting a foul putrid odor, whole crown collapses if left untreated.",
            "management": [
                "In early stages, scoop out the rotten spindle tissue carefully.",
                "Apply 10% Bordeaux paste or Copper Oxychloride paste directly onto the scooped apical point.",
                "Cover treated bud with a protective polythene cone to prevent rainwater wash-off.",
                "If palm is completely dead, fell and incinerate to protect adjacent palms."
            ]
        },
        "YELLOW_LEAF": {
            "common_name": "Yellow Leaf Disease (YLD)",
            "causative_agent": "Candidatus Phytoplasma arecae (vector-transmitted)",
            "season": "Year-round, progressive decline",
            "symptoms": "Yellowing starts from innermost whorl leaves spreading outward, leaves become brittle and crinkled, kernel inside nut blackens and shrivels.",
            "management": [
                "Soil nutrient balance: Apply 100g N, 40g P2O5, 140g K2O per palm/year, along with 1 kg neem cake and 12 kg organic compost.",
                "Micronutrient foliar correction: Spray Zinc Sulphate (0.5%), Magnesium Sulphate (0.5%), and Borax (0.2%).",
                "Ensure robust organic matter mulching and sub-surface drainage.",
                "Rogue out and destroy severely diseased, non-bearing palms."
            ]
        },
        "RING_SPOT": {
            "common_name": "Ring Spot Disease",
            "causative_agent": "Fungal complex",
            "season": "Post-monsoon and humid spells",
            "symptoms": "Discrete circular chlorotic spots on leaves, turning greyish-brown with yellow halo, premature frond drying.",
            "management": [
                "Foliar spray of Mancozeb (0.2%) or Copper Oxychloride (0.25%) on both sides of fronds.",
                "Prune and safely burn heavily diseased dried lower fronds.",
                "Maintain balanced potash fertilization to boost plant epidermal strength."
            ]
        }
    }
}

def get_knowledge_summary() -> str:
    """Return a concise prompt-friendly text summary of the knowledge base."""
    lines = [
        "ARECANUT & SNAIL AGRONOMIC KNOWLEDGE BASE:",
        "Crop: Arecanut (Areca catechu L.)",
        "1. Pest: Giant African Snail (Lissachatina fulica) - nocturnal invasive pest causing leaf scraping, tender stem gouging, and seedling destruction.",
        "   - Control: Hand-picking at dawn with salt/soap water disposal, Iron Phosphate / Metaldehyde baits under shade tiles, Copper tape or ash trunk rings.",
        "2. Disease: Koleroga (Mahali / Fruit Rot by Phytophthora meadii) - water-soaked lesions, premature nut drop. Spray 1% Bordeaux mixture pre-monsoon, cover bunches with 100-gauge polybags.",
        "3. Disease: Bud Rot (Phytophthora meadii) - yellowing spindle, rotting central crown, foul odor. Scoop rot, apply 10% Bordeaux paste, protect with rain cap.",
        "4. Disease: Yellow Leaf Disease (YLD, Phytoplasma) - progressive leaf yellowing, kernel blackening. Balanced NPK+Mg+Zn, 1kg neem cake, soil drainage.",
        "5. Disease: Ring Spot - circular lesions with yellow halo. Spray Mancozeb (0.2%) or Copper Oxychloride (0.25%)."
    ]
    return "\n".join(lines)
