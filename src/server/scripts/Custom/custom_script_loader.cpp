/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 */

// The generated static ScriptLoader expects one loader entry point per script
// module. The Custom module is enabled even when no custom scripts are present,
// so provide a no-op loader to satisfy the linker.
void AddCustomScripts()
{
}
