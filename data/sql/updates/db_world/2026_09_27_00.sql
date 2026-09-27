-- Initial MoP Mastery spell-script bindings.
-- Scripts remain gated by their specialization Mastery passive in C++.

DELETE FROM `spell_script_names` WHERE `ScriptName` IN (
    'spell_mastery_unshackled_fury',
    'spell_mastery_shield_discipline',
    'spell_mastery_blood_shield',
    'spell_mastery_ignite',
    'spell_mastery_hand_of_light',
    'spell_mastery_elemental_overload'
);

INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES
-- Warrior: Unshackled Fury (Enrage)
(12880, 'spell_mastery_unshackled_fury'),

-- Priest: Shield Discipline
(17,     'spell_mastery_shield_discipline'),
(123258, 'spell_mastery_shield_discipline'),
(114908, 'spell_mastery_shield_discipline'),
(114214, 'spell_mastery_shield_discipline'),
(47753,  'spell_mastery_shield_discipline'),

-- Death Knight: Blood Shield (Death Strike heal)
(45470,  'spell_mastery_blood_shield'),

-- Mage: Ignite
(133,    'spell_mastery_ignite'),
(44614,  'spell_mastery_ignite'),
(108853, 'spell_mastery_ignite'),
(2948,   'spell_mastery_ignite'),
(11366,  'spell_mastery_ignite'),

-- Paladin: Hand of Light
(35395,  'spell_mastery_hand_of_light'),
(53595,  'spell_mastery_hand_of_light'),
(24275,  'spell_mastery_hand_of_light'),
(85256,  'spell_mastery_hand_of_light'),
(53385,  'spell_mastery_hand_of_light'),

-- Shaman: Elemental Overload
(403,    'spell_mastery_elemental_overload'),
(421,    'spell_mastery_elemental_overload'),
(51505,  'spell_mastery_elemental_overload'),
(117014, 'spell_mastery_elemental_overload');
