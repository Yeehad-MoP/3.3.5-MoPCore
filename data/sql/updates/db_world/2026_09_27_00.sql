-- MoP Mastery spell-script bindings.
-- Passive mastery scripts use the converted 3.3.5 Spell.dbc layout supplied by the client.
-- Scripts remain gated by the active specialization Mastery passive in C++.

DELETE FROM `spell_script_names` WHERE `ScriptName` IN (
    'spell_mastery_strikes_of_opportunity',
    'spell_mastery_wild_quiver',
    'spell_mastery_main_gauche',
    'spell_mastery_critical_block',
    'spell_mastery_divine_bulwark',
    'spell_mastery_essence_of_the_viper',
    'spell_mastery_potent_poisons',
    'spell_mastery_executioner',
    'spell_mastery_shield_discipline_passive',
    'spell_mastery_frozen_heart',
    'spell_mastery_dreadblade',
    'spell_mastery_enhanced_elements',
    'spell_mastery_potent_afflictions',
    'spell_mastery_total_eclipse',
    'spell_mastery_razor_claws',
    'spell_mastery_natures_guardian',
    'spell_mastery_unshackled_fury',
    'spell_mastery_shield_discipline',
    'spell_mastery_blood_shield',
    'spell_mastery_ignite',
    'spell_mastery_hand_of_light',
    'spell_mastery_elemental_overload',
    'spell_mastery_illuminated_healing',
    'spell_mastery_echo_of_light',
    'spell_mastery_shadowy_recall',
    'spell_mastery_harmony_passive',
    'spell_mastery_harmony_periodic_bonus',
    'spell_mastery_harmony_trigger'
);

INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES
-- Warrior mastery passives
(76838, 'spell_mastery_strikes_of_opportunity'),
(76857, 'spell_mastery_critical_block'),
-- Fury mastery modifies the Enrage aura itself
(12880, 'spell_mastery_unshackled_fury'),

-- Paladin mastery passives / triggers
(76669, 'spell_mastery_illuminated_healing'),
(76671, 'spell_mastery_divine_bulwark'),
(35395, 'spell_mastery_hand_of_light'),
(53595, 'spell_mastery_hand_of_light'),
(24275, 'spell_mastery_hand_of_light'),
(85256, 'spell_mastery_hand_of_light'),
(53385, 'spell_mastery_hand_of_light'),

-- Hunter mastery passives
(76659, 'spell_mastery_wild_quiver'),
(76658, 'spell_mastery_essence_of_the_viper'),

-- Rogue mastery passives
(76803, 'spell_mastery_potent_poisons'),
(76806, 'spell_mastery_main_gauche'),
(76808, 'spell_mastery_executioner'),

-- Priest mastery passives + absorb triggers
(77484, 'spell_mastery_shield_discipline_passive'),
(77485, 'spell_mastery_echo_of_light'),
(77486, 'spell_mastery_shadowy_recall'),
(17,     'spell_mastery_shield_discipline'),
(123258, 'spell_mastery_shield_discipline'),
(114908, 'spell_mastery_shield_discipline'),
(114214, 'spell_mastery_shield_discipline'),
(47753,  'spell_mastery_shield_discipline'),

-- Death Knight mastery passives / trigger
(77514, 'spell_mastery_frozen_heart'),
(77515, 'spell_mastery_dreadblade'),
(45470, 'spell_mastery_blood_shield'),

-- Shaman mastery passives / triggers
(77223, 'spell_mastery_enhanced_elements'),
(403,    'spell_mastery_elemental_overload'),
(421,    'spell_mastery_elemental_overload'),
(51505,  'spell_mastery_elemental_overload'),
(117014, 'spell_mastery_elemental_overload'),

-- Mage Ignite triggers
(133,    'spell_mastery_ignite'),
(44614,  'spell_mastery_ignite'),
(108853, 'spell_mastery_ignite'),
(2948,   'spell_mastery_ignite'),
(11366,  'spell_mastery_ignite'),

-- Warlock mastery passive
(77215, 'spell_mastery_potent_afflictions'),

-- Druid mastery passives / Harmony direct-heal triggers
(77492,  'spell_mastery_total_eclipse'),
(77493,  'spell_mastery_razor_claws'),
(77494,  'spell_mastery_natures_guardian'),
(77495,  'spell_mastery_harmony_passive'),
(100977, 'spell_mastery_harmony_periodic_bonus'),
(-5185,  'spell_mastery_harmony_trigger'),
(-8936,  'spell_mastery_harmony_trigger'),
(18562,  'spell_mastery_harmony_trigger'),
(50464,  'spell_mastery_harmony_trigger');
