#!/usr/bin/env python3
from pathlib import Path

SPELL_HANDLER = Path("src/server/game/Handlers/SpellHandler.cpp")


def replace_once(text, old, new, label):
    if new in text:
        print(f"{label}: already applied")
        return text
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {text.count(old)}")
    print(f"{label}: patched")
    return text.replace(old, new, 1)


def main():
    text = SPELL_HANDLER.read_text(encoding="utf-8")

    # Stage 1 initially gated the suppression on _player->isMoving(). That is
    # too late for the 3.3.5 client: CMSG_CANCEL_CAST can arrive before the
    # movement opcode has updated the server-side movement state. Suppress the
    # legacy cancel whenever the referenced active spell is actually covered
    # by MoP Aura 330, independent of packet ordering.
    old_stage1 = """    // The 3.3.5 client does not understand MoP SPELL_AURA_CAST_WHILE_WALKING
    // and can send CMSG_CANCEL_CAST as soon as movement begins. The server is
    // authoritative for Aura 330, so ignore that movement-generated cancel
    // only when the active spell is actually affected by the aura.
    if (_player->isMoving())
        if (Spell* currentSpell = _player->FindCurrentSpellBySpellId(spellId))
            if (_player->HasAuraTypeWithAffectMask(SPELL_AURA_CAST_WHILE_WALKING, currentSpell->m_spellInfo))
                return;

"""

    new_stage2 = """    // The 3.3.5 client does not understand MoP SPELL_AURA_CAST_WHILE_WALKING
    // and can send CMSG_CANCEL_CAST before its movement opcode reaches the
    // server. Do not depend on _player->isMoving() here: packet ordering can
    // otherwise cancel a valid Aura 330 cast before movement state is updated.
    if (Spell* currentSpell = _player->FindCurrentSpellBySpellId(spellId))
        if (_player->HasAuraTypeWithAffectMask(SPELL_AURA_CAST_WHILE_WALKING, currentSpell->m_spellInfo))
            return;

"""

    if new_stage2 in text:
        print("Aura 330 packet-order cancel suppression: already applied")
    elif old_stage1 in text:
        text = text.replace(old_stage1, new_stage2, 1)
        print("Aura 330 packet-order cancel suppression: upgraded")
    else:
        # Allow applying directly to an unpatched SpellHandler.cpp too.
        old = """    recvPacket >> spellId;

    _player->SpellQueue.clear();
"""
        new = """    recvPacket >> spellId;

""" + new_stage2 + """    _player->SpellQueue.clear();
"""
        text = replace_once(text, old, new, "Aura 330 packet-order cancel suppression")

    SPELL_HANDLER.write_text(text, encoding="utf-8", newline="\n")
    print("Aura 330 client cancel suppression no longer depends on movement packet ordering.")


if __name__ == "__main__":
    main()
