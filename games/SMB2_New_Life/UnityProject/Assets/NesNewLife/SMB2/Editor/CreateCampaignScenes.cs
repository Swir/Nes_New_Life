#if UNITY_EDITOR
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace NesNewLife.SMB2.EditorTools
{
    public static class CreateCampaignScenes
    {
        public const string StageDirectory = "Assets/NesNewLife/SMB2/Campaign";
        public static readonly string[] StagePaths = BuildStagePaths();

        [MenuItem("NES New Life/SMB2/Create 20-Stage Campaign")]
        public static void Create()
        {
            Directory.CreateDirectory(StageDirectory);
            CreatePrototypeScene.CreatePlayable();
            const string sourcePath = "Assets/NesNewLife/SMB2/Prototype/SMB2_Playable.unity";
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            if (!File.Exists(sourcePath))
            {
                Debug.LogError("NES New Life: base playable scene was not generated; campaign creation aborted.");
                return;
            }

            for (int i = 0; i < StagePaths.Length; i++)
            {
                string stagePath = StagePaths[i];
                if (AssetDatabase.LoadAssetAtPath<SceneAsset>(stagePath) != null)
                    AssetDatabase.DeleteAsset(stagePath);

                if (!AssetDatabase.CopyAsset(sourcePath, stagePath))
                {
                    Debug.LogError($"NES New Life: failed to create {stagePath}.");
                    return;
                }

                ConfigureStage(stagePath, i + 1);
            }

            List<EditorBuildSettingsScene> buildScenes = new List<EditorBuildSettingsScene>();
            foreach (string path in StagePaths)
                buildScenes.Add(new EditorBuildSettingsScene(path, true));
            EditorBuildSettings.scenes = buildScenes.ToArray();

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            EditorSceneManager.OpenScene(StagePaths[0]);
            Debug.Log($"NES New Life: {CampaignCatalog.StageCount}-stage / {CampaignCatalog.WorldCount}-world campaign generated and registered in Build Settings.");
        }

        private static string[] BuildStagePaths()
        {
            string[] paths = new string[CampaignCatalog.StageCount];
            for (int i = 0; i < paths.Length; i++)
                paths[i] = $"{StageDirectory}/{CampaignCatalog.SceneForStage(i + 1)}.unity";
            return paths;
        }

        private static void ConfigureStage(string path, int stageNumber)
        {
            var scene = EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
            int world = CampaignCatalog.WorldForStage(stageNumber);
            int level = CampaignCatalog.LevelForStage(stageNumber);

            CampaignStageDefinition definition = Object.FindFirstObjectByType<CampaignStageDefinition>();
            if (definition == null)
            {
                GameObject stageObject = new GameObject("Campaign Stage");
                definition = stageObject.AddComponent<CampaignStageDefinition>();
            }

            bool finalStage = stageNumber == CampaignCatalog.StageCount;
            string nextScene = finalStage ? string.Empty : CampaignCatalog.SceneForStage(stageNumber + 1);
            int completionBonus = 1500 + world * 750 + level * 500;
            definition.Configure(stageNumber, CampaignCatalog.DisplayNameForStage(stageNumber), nextScene, finalStage, completionBonus);

            ApplyVisualVariant(stageNumber, world, level);
            ApplyDifficultyVariant(stageNumber, world, level);
            ApplyTraversalAndHazardVariant(stageNumber, world, level);
            ApplyWorldIdentity(stageNumber, world, level);
            EditorSceneManager.SaveScene(scene, path);
        }

        private static void ApplyVisualVariant(int stageNumber, int world, int level)
        {
            Color[] skies =
            {
                new Color(0.035f, 0.075f, 0.12f),
                new Color(0.075f, 0.050f, 0.12f),
                new Color(0.035f, 0.105f, 0.10f),
                new Color(0.10f, 0.075f, 0.035f),
                new Color(0.10f, 0.035f, 0.070f),
                new Color(0.045f, 0.045f, 0.11f),
                new Color(0.12f, 0.025f, 0.035f)
            };
            Color[] backdrops =
            {
                new Color(0.08f, 0.15f, 0.22f),
                new Color(0.15f, 0.10f, 0.21f),
                new Color(0.07f, 0.18f, 0.16f),
                new Color(0.20f, 0.15f, 0.08f),
                new Color(0.20f, 0.08f, 0.14f),
                new Color(0.09f, 0.09f, 0.20f),
                new Color(0.22f, 0.06f, 0.08f)
            };

            Camera camera = Object.FindFirstObjectByType<Camera>();
            if (camera != null)
                camera.backgroundColor = skies[Mathf.Clamp(world - 1, 0, skies.Length - 1)] + new Color(level * 0.004f, 0f, level * 0.003f, 0f);

            foreach (SpriteRenderer renderer in Object.FindObjectsByType<SpriteRenderer>(FindObjectsSortMode.None))
            {
                if (renderer.name.Contains("Backdrop"))
                    renderer.color = backdrops[Mathf.Clamp(world - 1, 0, backdrops.Length - 1)];
            }
        }

        private static void ApplyDifficultyVariant(int stageNumber, int world, int level)
        {
            BossController boss = Object.FindFirstObjectByType<BossController>();
            if (boss != null)
            {
                EnemyHealth health = boss.GetComponent<EnemyHealth>();
                if (health != null)
                    health.Configure(3 + world + level, 1000 + world * 600 + level * 400);
            }

            EnemyPatroller[] patrollers = Object.FindObjectsByType<EnemyPatroller>(FindObjectsSortMode.None);
            for (int i = 0; i < patrollers.Length; i++)
            {
                Rigidbody2D body = patrollers[i].GetComponent<Rigidbody2D>();
                if (body != null)
                    body.gravityScale = 3f + world * 0.08f + level * 0.04f;
            }

            List<GameObject> platforms = new List<GameObject>();
            foreach (BoxCollider2D collider in Object.FindObjectsByType<BoxCollider2D>(FindObjectsSortMode.None))
            {
                if (collider.gameObject.name == "Platform")
                    platforms.Add(collider.gameObject);
            }

            platforms.Sort((a, b) => a.transform.position.x.CompareTo(b.transform.position.x));
            float amplitude = Mathf.Min(1.4f, (world - 1) * 0.16f + (level - 1) * 0.22f);
            for (int i = 0; i < platforms.Count; i++)
            {
                Vector3 position = platforms[i].transform.position;
                position.y += (i % 2 == 0 ? 1f : -1f) * amplitude;
                platforms[i].transform.position = position;
            }
        }

        private static void ApplyTraversalAndHazardVariant(int stageNumber, int world, int level)
        {
            Sprite sprite = FindPrototypeSprite();
            if (sprite == null)
            {
                Debug.LogWarning($"NES New Life: Stage {stageNumber} traversal pass skipped because no prototype sprite was found.");
                return;
            }

            // Every stage receives a vertical route; later worlds layer moving/crumbling traversal on top.
            float climbX = 18.5f + level * 1.5f;
            float climbHeight = 4.4f + world * 0.35f;
            CreateClimbable(new Vector2(climbX, 1.2f), new Vector2(0.7f, climbHeight), sprite);
            CreateGroundLedge(new Vector2(climbX, 3.5f + world * 0.18f), new Vector2(3.0f, 0.45f), sprite);

            if (world >= 2 || level >= 2)
            {
                CreateMovingPlatform(new Vector2(36.0f + level, -0.6f), new Vector2(2.6f, 0.45f),
                    new Vector2(0f, 3.0f + world * 0.35f), 1.4f + world * 0.18f + level * 0.1f, sprite);
            }

            if (world >= 3 || level == 3)
                CreateCrumblePlatform(new Vector2(41.0f + level * 0.4f, 1.1f), new Vector2(2.4f, 0.42f), sprite);

            int spikeCount = Mathf.Clamp(world - 1 + (level == 3 ? 1 : 0), 0, 4);
            for (int i = 0; i < spikeCount; i++)
                CreateSpikes(new Vector2(44.0f + i * 2.0f, -1.72f), new Vector2(1.25f, 0.35f), sprite);

            if (world >= 4)
            {
                CreateMovingPlatform(new Vector2(46.0f, 1.0f + (level - 1) * 0.7f), new Vector2(2.2f, 0.42f),
                    new Vector2(3.0f + world * 0.25f, 0f), 2.0f + world * 0.15f, sprite);
            }

            if (world >= 5)
            {
                CreateCrumblePlatform(new Vector2(49.0f, 2.2f), new Vector2(2.0f, 0.40f), sprite);
                CreateClimbable(new Vector2(50.5f, 2.2f), new Vector2(0.7f, 5.6f), sprite);
            }

            if (CampaignCatalog.IsWorldFinale(stageNumber))
            {
                LevelExit exit = Object.FindFirstObjectByType<LevelExit>();
                if (exit != null && world >= 2)
                    exit.transform.position = new Vector3(53f, 4.2f + world * 0.3f, exit.transform.position.z);

                if (world >= 2)
                {
                    CreateClimbable(new Vector2(52.6f, 1.7f), new Vector2(0.8f, 6.8f + world * 0.2f), sprite);
                    CreateGroundLedge(new Vector2(52.6f, 4.3f + world * 0.3f), new Vector2(4.4f, 0.5f), sprite);
                }
            }

            if (CampaignCatalog.IsWorldFinale(stageNumber) && world >= 3)
                ReplaceGuardianWithChargeBoss(world, stageNumber == CampaignCatalog.StageCount);
        }

        private static void ApplyWorldIdentity(int stageNumber, int world, int level)
        {
            Sprite sprite = FindPrototypeSprite();
            if (sprite == null)
                return;

            // Public-safe geometric landmarks make generated worlds visually distinguishable.
            Color landmarkColor = Color.HSVToRGB((world - 1) / 7f, 0.42f, 0.78f);
            int landmarkCount = 2 + level;
            for (int i = 0; i < landmarkCount; i++)
            {
                float x = -15f + i * (12f / Mathf.Max(1, landmarkCount - 1));
                float y = 2.8f + ((i + world) % 2) * 1.25f;
                GameObject marker = CreateBlock($"World {world} Landmark {i + 1}", new Vector2(x, y),
                    new Vector2(0.45f + world * 0.04f, 1.5f + level * 0.25f), landmarkColor, sprite);
                marker.GetComponent<SpriteRenderer>().sortingOrder = -2;
            }
        }

        private static Sprite FindPrototypeSprite()
        {
            PlayerController2D player = Object.FindFirstObjectByType<PlayerController2D>();
            if (player != null)
            {
                SpriteRenderer renderer = player.GetComponent<SpriteRenderer>();
                if (renderer != null && renderer.sprite != null)
                    return renderer.sprite;
            }

            foreach (SpriteRenderer renderer in Object.FindObjectsByType<SpriteRenderer>(FindObjectsSortMode.None))
            {
                if (renderer.sprite != null)
                    return renderer.sprite;
            }
            return null;
        }

        private static void CreateClimbable(Vector2 position, Vector2 size, Sprite sprite)
        {
            GameObject vine = CreateBlock("Climbable Vine", position, size, new Color(0.22f, 0.72f, 0.38f, 0.72f), sprite);
            vine.GetComponent<SpriteRenderer>().sortingOrder = -1;
            BoxCollider2D collider = vine.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            vine.AddComponent<ClimbableZone2D>();
        }

        private static void CreateGroundLedge(Vector2 position, Vector2 size, Sprite sprite)
        {
            GameObject ledge = CreateBlock("Vertical Ledge", position, size, new Color(0.31f, 0.45f, 0.54f), sprite);
            ledge.layer = 8;
            ledge.AddComponent<BoxCollider2D>();
        }

        private static void CreateMovingPlatform(Vector2 position, Vector2 size, Vector2 travel, float speed, Sprite sprite)
        {
            GameObject platform = CreateBlock("Moving Platform", position, size, new Color(0.34f, 0.70f, 0.92f), sprite);
            platform.layer = 8;
            Rigidbody2D body = platform.AddComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.freezeRotation = true;
            platform.AddComponent<BoxCollider2D>();
            MovingPlatform2D mover = platform.AddComponent<MovingPlatform2D>();
            mover.Configure(travel, speed);
        }

        private static void CreateCrumblePlatform(Vector2 position, Vector2 size, Sprite sprite)
        {
            GameObject platform = CreateBlock("Crumble Platform", position, size, new Color(0.88f, 0.56f, 0.25f), sprite);
            platform.layer = 8;
            platform.AddComponent<BoxCollider2D>();
            platform.AddComponent<CrumblePlatform2D>();
        }

        private static void CreateSpikes(Vector2 position, Vector2 size, Sprite sprite)
        {
            GameObject spikes = CreateBlock("Spike Hazard", position, size, new Color(0.95f, 0.22f, 0.30f), sprite);
            BoxCollider2D collider = spikes.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            spikes.AddComponent<SpikeHazard2D>();
        }

        private static void ReplaceGuardianWithChargeBoss(int world, bool finalBoss)
        {
            BossController oldBoss = Object.FindFirstObjectByType<BossController>();
            if (oldBoss == null)
                return;

            GameObject bossObject = oldBoss.gameObject;
            Object.DestroyImmediate(oldBoss);
            ChargeBossController chargeBoss = bossObject.AddComponent<ChargeBossController>();
            chargeBoss.Configure(41f, 51f, Mathf.Clamp(1.05f + world * 0.07f, 1f, 1.65f));

            SpriteRenderer renderer = bossObject.GetComponent<SpriteRenderer>();
            if (renderer != null)
                renderer.color = finalBoss ? new Color(1f, 0.18f, 0.36f) : new Color(0.92f, 0.23f, 0.60f);

            EnemyHealth health = bossObject.GetComponent<EnemyHealth>();
            if (health != null)
                health.Configure(finalBoss ? 16 : 6 + world, finalBoss ? 12000 : 2500 + world * 900);

            bossObject.name = finalBoss ? "Final Dreambreaker Guardian" : $"World {world} Charge Guardian";
        }

        private static GameObject CreateBlock(string name, Vector2 position, Vector2 size, Color color, Sprite sprite)
        {
            GameObject obj = new GameObject(name);
            obj.transform.position = position;
            obj.transform.localScale = new Vector3(size.x, size.y, 1f);
            SpriteRenderer renderer = obj.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.color = color;
            return obj;
        }
    }
}
#endif
