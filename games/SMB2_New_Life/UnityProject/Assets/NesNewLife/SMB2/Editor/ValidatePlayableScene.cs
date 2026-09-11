#if UNITY_EDITOR
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace NesNewLife.SMB2.EditorTools
{
    public static class ValidatePlayableScene
    {
        [MenuItem("NES New Life/SMB2/Validate PLAYABLE Scene")]
        public static void Validate()
        {
            List<string> errors = new List<string>();
            List<string> warnings = new List<string>();

            Require<GameManager>(errors, "GameManager");
            Require<GameHud>(errors, "GameHud");
            Require<PlayerController2D>(errors, "PlayerController2D");
            Require<PlayerHealth>(errors, "PlayerHealth");
            Require<PlayerInventory>(errors, "PlayerInventory");
            Require<CameraFollow2D>(errors, "CameraFollow2D");
            Require<LevelExit>(errors, "LevelExit");
            Require<BossController>(errors, "BossController");

            if (Object.FindObjectsByType<DoorPortal>(FindObjectsSortMode.None).Length < 3)
                errors.Add("Expected at least 3 DoorPortal components for the surface/sub-area route.");
            if (Object.FindObjectsByType<KeyPickup>(FindObjectsSortMode.None).Length < 1)
                errors.Add("Expected at least one KeyPickup.");
            if (Object.FindObjectsByType<CheckpointTrigger>(FindObjectsSortMode.None).Length < 1)
                warnings.Add("No checkpoint found.");
            if (Object.FindObjectsByType<CarryableObject2D>(FindObjectsSortMode.None).Length < 5)
                warnings.Add("Low carryable-object count; boss route may be less forgiving.");

            int patrollers = Object.FindObjectsByType<EnemyPatroller>(FindObjectsSortMode.None).Length;
            if (patrollers < 4)
                warnings.Add($"Only {patrollers} base patrollers found.");

            string report = $"SMB2 playable-scene validation: {errors.Count} error(s), {warnings.Count} warning(s).";
            if (warnings.Count > 0)
                report += "\nWarnings:\n- " + string.Join("\n- ", warnings);

            if (errors.Count > 0)
            {
                report += "\nErrors:\n- " + string.Join("\n- ", errors);
                Debug.LogError(report);
                EditorUtility.DisplayDialog("SMB2 validation FAILED", report, "OK");
                return;
            }

            Debug.Log(report);
            EditorUtility.DisplayDialog("SMB2 validation passed", report, "OK");
        }

        private static void Require<T>(List<string> errors, string label) where T : Object
        {
            if (Object.FindFirstObjectByType<T>() == null)
                errors.Add($"Missing required component: {label}.");
        }
    }
}
#endif
