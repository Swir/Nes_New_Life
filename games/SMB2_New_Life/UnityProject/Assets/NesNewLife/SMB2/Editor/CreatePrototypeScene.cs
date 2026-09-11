#if UNITY_EDITOR
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace NesNewLife.SMB2.EditorTools
{
    public static class CreatePrototypeScene
    {
        private const string SceneDirectory = "Assets/NesNewLife/SMB2/Prototype";
        private const string ScenePath = SceneDirectory + "/SMB2_Playable.unity";
        private const string GeneratedDirectory = "Assets/NesNewLife/SMB2/Generated";
        private const string GeneratedSpritePath = GeneratedDirectory + "/PrototypeSquare.png";
        private const int GroundLayer = 8;
        private const int CarryableLayer = 9;

        [MenuItem("NES New Life/SMB2/Create PLAYABLE Level")]
        public static void CreatePlayable()
        {
            Sprite sprite = GetOrCreatePrototypeSprite();
            if (sprite == null)
            {
                Debug.LogError("NES New Life: failed to create the prototype sprite asset.");
                return;
            }

            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            CreateManagers();
            CreateBackdrop(sprite);

            // MAIN ROUTE
            CreateGroundAt(-18f, -2.5f, 10f, sprite, new Color(0.15f, 0.22f, 0.30f));
            CreateGroundAt(-5f, -2.5f, 12f, sprite, new Color(0.15f, 0.22f, 0.30f));
            CreateGroundAt(10f, -2.5f, 14f, sprite, new Color(0.15f, 0.22f, 0.30f));
            CreateGroundAt(23f, -2.5f, 10f, sprite, new Color(0.15f, 0.22f, 0.30f));
            CreateGroundAt(42f, -2.5f, 27f, sprite, new Color(0.15f, 0.22f, 0.30f));

            CreatePlatform(new Vector2(-12f, -0.2f), new Vector2(4f, 0.55f), sprite);
            CreatePlatform(new Vector2(-2f, 1.0f), new Vector2(4f, 0.55f), sprite);
            CreatePlatform(new Vector2(8f, 2.0f), new Vector2(5f, 0.55f), sprite);
            CreatePlatform(new Vector2(21f, 0.4f), new Vector2(5f, 0.55f), sprite);
            CreatePlatform(new Vector2(40f, 1.8f), new Vector2(5f, 0.55f), sprite);
            CreatePlatform(new Vector2(50f, 3.0f), new Vector2(5f, 0.55f), sprite);

            // This tall barrier makes the underground key route mandatory.
            CreateBarrier(new Vector2(29f, 2f), new Vector2(1.2f, 12f), sprite);

            GameObject player = CreatePlayer(new Vector2(-21f, -1.15f), sprite);

            CreateCarryable(new Vector2(-16.5f, -1.55f), sprite, new Color(0.98f, 0.54f, 0.18f));
            CreatePullablePlant(new Vector2(-6f, -1.72f), sprite, new Color(0.95f, 0.31f, 0.24f));
            CreatePullablePlant(new Vector2(4f, -1.72f), sprite, new Color(0.85f, 0.40f, 0.92f));
            CreateCarryable(new Vector2(19f, -1.55f), sprite, new Color(0.98f, 0.70f, 0.20f));
            CreatePullablePlant(new Vector2(38f, -1.72f), sprite, new Color(0.34f, 0.82f, 0.64f));
            CreateCarryable(new Vector2(44f, -1.55f), sprite, new Color(0.95f, 0.56f, 0.18f));
            CreateCarryable(new Vector2(51f, -1.55f), sprite, new Color(0.42f, 0.76f, 1f));

            CreateEnemy(new Vector2(-11.5f, 0.55f), -13.5f, -10.5f, 1.6f, sprite);
            CreateEnemy(new Vector2(1f, -1.35f), -1f, 4f, 2.0f, sprite);
            CreateEnemy(new Vector2(9f, 2.7f), 6.2f, 10.2f, 1.9f, sprite);
            CreateEnemy(new Vector2(20f, -1.35f), 17f, 25f, 2.3f, sprite);
            CreateEnemy(new Vector2(39f, 2.5f), 36.5f, 41.5f, 2.1f, sprite);
            CreateBoss(new Vector2(50f, -1.0f), 44f, 54f, sprite);

            CreateScorePickup(new Vector2(-12f, 1.0f), sprite);
            CreateScorePickup(new Vector2(-2f, 2.0f), sprite);
            CreateScorePickup(new Vector2(8f, 3.0f), sprite);
            CreateScorePickup(new Vector2(21f, 1.4f), sprite);
            CreateScorePickup(new Vector2(40f, 2.8f), sprite);
            CreateScorePickup(new Vector2(50f, 4.0f), sprite);
            CreateHeart(new Vector2(6f, -1.3f), sprite);
            CreateHeart(new Vector2(40f, -1.3f), sprite);

            // UNDERGROUND SUB-AREA
            CreateGroundAt(18f, -20.5f, 24f, sprite, new Color(0.12f, 0.13f, 0.19f));
            CreateBarrier(new Vector2(6f, -16f), new Vector2(1f, 10f), sprite);
            CreateBarrier(new Vector2(30f, -16f), new Vector2(1f, 10f), sprite);
            CreatePlatform(new Vector2(12f, -17.3f), new Vector2(4f, 0.55f), sprite, new Color(0.26f, 0.28f, 0.36f));
            CreatePlatform(new Vector2(18f, -15.4f), new Vector2(4f, 0.55f), sprite, new Color(0.26f, 0.28f, 0.36f));
            CreatePlatform(new Vector2(24f, -17.0f), new Vector2(4f, 0.55f), sprite, new Color(0.26f, 0.28f, 0.36f));
            CreateEnemy(new Vector2(14f, -19.35f), 10f, 17f, 2.0f, sprite);
            CreateEnemy(new Vector2(23f, -19.35f), 20f, 27f, 2.2f, sprite);
            CreatePullablePlant(new Vector2(11f, -19.72f), sprite, new Color(0.64f, 0.42f, 0.94f));
            CreatePullablePlant(new Vector2(25f, -19.72f), sprite, new Color(0.88f, 0.48f, 0.28f));
            CreateScorePickup(new Vector2(12f, -16.25f), sprite);
            CreateScorePickup(new Vector2(24f, -15.95f), sprite);
            CreateKey(new Vector2(18f, -14.55f), sprite);
            CreateHeart(new Vector2(18f, -19.3f), sprite);

            Transform undergroundEntry = CreateMarker("Underground Entry Spawn", new Vector2(9f, -19.1f));
            Transform mainDoorReturn = CreateMarker("Main Door Return", new Vector2(13f, -1.25f));
            Transform postBarrierSpawn = CreateMarker("Post Barrier Spawn", new Vector2(34f, -1.25f));

            CreateDoor("Door_To_Underground", new Vector2(13f, -1.0f), undergroundEntry, false, sprite, new Color(0.30f, 0.66f, 0.95f));
            CreateDoor("Door_Back_To_Surface", new Vector2(9f, -18.8f), mainDoorReturn, false, sprite, new Color(0.30f, 0.66f, 0.95f));
            CreateDoor("LOCKED_Door_To_LateRoute", new Vector2(27f, -18.8f), postBarrierSpawn, true, sprite, new Color(0.95f, 0.68f, 0.18f));

            CreateCameraZone("Main Camera Zone", new Vector2(17f, 0f), new Vector2(86f, 12f));
            CreateCameraZone("Underground Camera Zone", new Vector2(18f, -16f), new Vector2(24f, 12f));

            CreateCheckpoint(new Vector2(36f, -1.15f), sprite);
            CreateExit(new Vector2(54.5f, -0.55f), sprite);
            CreateKillZone(new Vector2(16f, -8f), new Vector2(110f, 4f));
            CreateKillZone(new Vector2(18f, -25f), new Vector2(30f, 4f));
            CreateCamera(player.transform, new Rect(-26f, -6f, 86f, 12f));

            Directory.CreateDirectory(SceneDirectory);
            AssetDatabase.Refresh();
            EditorSceneManager.SaveScene(scene, ScenePath);
            EnsureSceneInBuildSettings();

            Selection.activeGameObject = player;
            EditorGUIUtility.PingObject(player);
            Debug.Log("NES New Life: multi-room SMB2 playable level created. Select 1-4, crouch + Shift to pull plants, explore the underground room, collect the key and unlock the late route.");
        }

        [MenuItem("NES New Life/SMB2/Create Prototype Scene")]
        public static void CreateLegacyMenuAlias() => CreatePlayable();

        private static Sprite GetOrCreatePrototypeSprite()
        {
            Sprite existing = AssetDatabase.LoadAssetAtPath<Sprite>(GeneratedSpritePath);
            if (existing != null)
                return existing;

            Directory.CreateDirectory(GeneratedDirectory);
            Texture2D texture = new Texture2D(16, 16, TextureFormat.RGBA32, false);
            Color[] pixels = new Color[16 * 16];
            for (int i = 0; i < pixels.Length; i++)
                pixels[i] = Color.white;
            texture.SetPixels(pixels);
            texture.Apply();
            File.WriteAllBytes(GeneratedSpritePath, texture.EncodeToPNG());
            Object.DestroyImmediate(texture);

            AssetDatabase.ImportAsset(GeneratedSpritePath, ImportAssetOptions.ForceSynchronousImport);
            TextureImporter importer = AssetImporter.GetAtPath(GeneratedSpritePath) as TextureImporter;
            if (importer != null)
            {
                importer.textureType = TextureImporterType.Sprite;
                importer.spritePixelsPerUnit = 16f;
                importer.filterMode = FilterMode.Point;
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.wrapMode = TextureWrapMode.Clamp;
                importer.SaveAndReimport();
            }

            return AssetDatabase.LoadAssetAtPath<Sprite>(GeneratedSpritePath);
        }

        private static void CreateManagers()
        {
            GameObject manager = new GameObject("GameManager");
            manager.AddComponent<GameManager>();
            GameObject hud = new GameObject("HUD");
            hud.AddComponent<GameHud>();
        }

        private static GameObject CreatePlayer(Vector2 position, Sprite sprite)
        {
            GameObject player = CreateBlock("Player", position, new Vector2(0.85f, 1.45f), CharacterTuning.For(CharacterType.Mario).Color, sprite);
            Rigidbody2D body = player.AddComponent<Rigidbody2D>();
            body.gravityScale = 3f;
            body.freezeRotation = true;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            BoxCollider2D collider = player.AddComponent<BoxCollider2D>();
            collider.size = new Vector2(0.9f, 1f);

            GameObject groundCheck = new GameObject("GroundCheck");
            groundCheck.transform.SetParent(player.transform);
            groundCheck.transform.localPosition = new Vector3(0f, -0.58f, 0f);
            GameObject pickupPoint = new GameObject("PickupPoint");
            pickupPoint.transform.SetParent(player.transform);
            pickupPoint.transform.localPosition = new Vector3(0f, -0.35f, 0f);
            GameObject carryAnchor = new GameObject("CarryAnchor");
            carryAnchor.transform.SetParent(player.transform);
            carryAnchor.transform.localPosition = new Vector3(0f, 0.95f, 0f);

            PlayerController2D controller = player.AddComponent<PlayerController2D>();
            SerializedObject controllerSO = new SerializedObject(controller);
            controllerSO.FindProperty("groundCheck").objectReferenceValue = groundCheck.transform;
            controllerSO.FindProperty("groundMask").intValue = 1 << GroundLayer;
            controllerSO.ApplyModifiedPropertiesWithoutUndo();

            CarrySystem2D carry = player.AddComponent<CarrySystem2D>();
            SerializedObject carrySO = new SerializedObject(carry);
            carrySO.FindProperty("pickupPoint").objectReferenceValue = pickupPoint.transform;
            carrySO.FindProperty("carryAnchor").objectReferenceValue = carryAnchor.transform;
            carrySO.FindProperty("carryableMask").intValue = 1 << CarryableLayer;
            carrySO.ApplyModifiedPropertiesWithoutUndo();

            player.AddComponent<PlayerHealth>();
            player.AddComponent<PlayerInventory>();
            return player;
        }

        private static void CreateEnemy(Vector2 position, float left, float right, float speed, Sprite sprite)
        {
            GameObject enemy = CreateBlock("Enemy_Patroller", position, new Vector2(0.9f, 0.9f), new Color(0.75f, 0.28f, 0.25f), sprite);
            Rigidbody2D body = enemy.AddComponent<Rigidbody2D>();
            body.gravityScale = 3f;
            body.freezeRotation = true;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            enemy.AddComponent<BoxCollider2D>();
            enemy.AddComponent<EnemyHealth>();
            enemy.AddComponent<DamageOnContact>();
            EnemyPatroller patrol = enemy.AddComponent<EnemyPatroller>();
            patrol.Configure(left, right, speed);
        }

        private static void CreateBoss(Vector2 position, float left, float right, Sprite sprite)
        {
            GameObject boss = CreateBlock("MINIBOSS", position, new Vector2(1.7f, 1.7f), new Color(0.72f, 0.20f, 0.85f), sprite);
            Rigidbody2D body = boss.AddComponent<Rigidbody2D>();
            body.gravityScale = 3.2f;
            body.freezeRotation = true;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            boss.AddComponent<BoxCollider2D>();
            EnemyHealth health = boss.AddComponent<EnemyHealth>();
            health.Configure(5, 2500);
            boss.AddComponent<DamageOnContact>();
            BossController controller = boss.AddComponent<BossController>();
            controller.Configure(left, right);
        }

        private static CarryableObject2D CreateCarryable(Vector2 position, Sprite sprite, Color color)
        {
            GameObject obj = CreateBlock("Carryable", position, new Vector2(0.55f, 0.55f), color, sprite);
            obj.layer = CarryableLayer;
            Rigidbody2D body = obj.AddComponent<Rigidbody2D>();
            body.gravityScale = 2.5f;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            obj.AddComponent<BoxCollider2D>();
            return obj.AddComponent<CarryableObject2D>();
        }

        private static void CreatePullablePlant(Vector2 position, Sprite sprite, Color payloadColor)
        {
            CarryableObject2D payload = CreateCarryable(position + Vector2.up * 0.35f, sprite, payloadColor);
            payload.name = "Pulled_Item";
            payload.gameObject.SetActive(false);

            GameObject plant = CreateBlock("Pullable_Plant", position, new Vector2(0.32f, 0.55f), new Color(0.28f, 0.82f, 0.32f), sprite);
            plant.layer = CarryableLayer;
            BoxCollider2D collider = plant.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            PullablePlant pullable = plant.AddComponent<PullablePlant>();
            pullable.Configure(payload);
        }

        private static void CreateKey(Vector2 position, Sprite sprite)
        {
            GameObject key = CreateBlock("KEY", position, new Vector2(0.38f, 0.72f), new Color(1f, 0.82f, 0.16f), sprite);
            BoxCollider2D collider = key.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            key.AddComponent<KeyPickup>();
        }

        private static void CreateDoor(string name, Vector2 position, Transform destination, bool requiresKey, Sprite sprite, Color color)
        {
            GameObject door = CreateBlock(name, position, new Vector2(1.25f, 2.5f), color, sprite);
            BoxCollider2D collider = door.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            DoorPortal portal = door.AddComponent<DoorPortal>();
            portal.Configure(destination, requiresKey, requiresKey);
        }

        private static Transform CreateMarker(string name, Vector2 position)
        {
            GameObject marker = new GameObject(name);
            marker.transform.position = position;
            return marker.transform;
        }

        private static void CreateCameraZone(string name, Vector2 center, Vector2 size)
        {
            GameObject zone = new GameObject(name);
            zone.transform.position = center;
            BoxCollider2D collider = zone.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            CameraZone cameraZone = zone.AddComponent<CameraZone>();
            cameraZone.Configure(center, size);
        }

        private static void CreateScorePickup(Vector2 position, Sprite sprite)
        {
            GameObject pickup = CreateBlock("ScorePickup", position, new Vector2(0.35f, 0.35f), new Color(1f, 0.88f, 0.22f), sprite);
            CircleCollider2D collider = pickup.AddComponent<CircleCollider2D>();
            collider.isTrigger = true;
            pickup.AddComponent<ScorePickup>();
        }

        private static void CreateHeart(Vector2 position, Sprite sprite)
        {
            GameObject heart = CreateBlock("Heart", position, new Vector2(0.48f, 0.48f), new Color(1f, 0.18f, 0.38f), sprite);
            CircleCollider2D collider = heart.AddComponent<CircleCollider2D>();
            collider.isTrigger = true;
            heart.AddComponent<HeartPickup>();
        }

        private static void CreateCheckpoint(Vector2 position, Sprite sprite)
        {
            GameObject checkpoint = CreateBlock("Checkpoint", position, new Vector2(0.35f, 2.6f), new Color(0.30f, 0.58f, 1f), sprite);
            BoxCollider2D collider = checkpoint.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            checkpoint.AddComponent<CheckpointTrigger>();
        }

        private static void CreateExit(Vector2 position, Sprite sprite)
        {
            GameObject exit = CreateBlock("LEVEL EXIT", position, new Vector2(1.6f, 3.4f), new Color(0.30f, 0.95f, 0.70f), sprite);
            BoxCollider2D collider = exit.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            exit.AddComponent<LevelExit>();
        }

        private static void CreateKillZone(Vector2 position, Vector2 size)
        {
            GameObject zone = new GameObject("Fall Kill Zone");
            zone.transform.position = position;
            BoxCollider2D collider = zone.AddComponent<BoxCollider2D>();
            collider.size = size;
            collider.isTrigger = true;
            zone.AddComponent<KillZone>();
        }

        private static void CreateGroundAt(float centerX, float centerY, float width, Sprite sprite, Color color)
        {
            GameObject ground = CreateBlock("Ground", new Vector2(centerX, centerY), new Vector2(width, 1f), color, sprite);
            ground.layer = GroundLayer;
            ground.AddComponent<BoxCollider2D>();
        }

        private static void CreatePlatform(Vector2 position, Vector2 scale, Sprite sprite)
        {
            CreatePlatform(position, scale, sprite, new Color(0.30f, 0.44f, 0.52f));
        }

        private static void CreatePlatform(Vector2 position, Vector2 scale, Sprite sprite, Color color)
        {
            GameObject platform = CreateBlock("Platform", position, scale, color, sprite);
            platform.layer = GroundLayer;
            platform.AddComponent<BoxCollider2D>();
        }

        private static void CreateBarrier(Vector2 position, Vector2 scale, Sprite sprite)
        {
            GameObject barrier = CreateBlock("World Barrier", position, scale, new Color(0.12f, 0.17f, 0.23f), sprite);
            barrier.layer = GroundLayer;
            barrier.AddComponent<BoxCollider2D>();
        }

        private static GameObject CreateBlock(string name, Vector2 position, Vector2 scale, Color color, Sprite sprite)
        {
            GameObject obj = new GameObject(name);
            obj.transform.position = position;
            obj.transform.localScale = new Vector3(scale.x, scale.y, 1f);
            SpriteRenderer renderer = obj.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.color = color;
            return obj;
        }

        private static void CreateBackdrop(Sprite sprite)
        {
            for (int i = 0; i < 9; i++)
            {
                float x = -22f + i * 10f;
                GameObject hill = CreateBlock("Backdrop", new Vector2(x, -0.2f), new Vector2(8f, 7f), new Color(0.08f + i * 0.006f, 0.12f, 0.20f), sprite);
                hill.GetComponent<SpriteRenderer>().sortingOrder = -20;
            }

            GameObject underground = CreateBlock("Underground Backdrop", new Vector2(18f, -16f), new Vector2(24f, 12f), new Color(0.035f, 0.04f, 0.075f), sprite);
            underground.GetComponent<SpriteRenderer>().sortingOrder = -20;
        }

        private static void CreateCamera(Transform target, Rect initialBounds)
        {
            GameObject cameraObject = new GameObject("Main Camera");
            cameraObject.tag = "MainCamera";
            cameraObject.transform.position = new Vector3(target.position.x, 0.5f, -10f);
            Camera camera = cameraObject.AddComponent<Camera>();
            camera.orthographic = true;
            camera.orthographicSize = 5.3f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.035f, 0.055f, 0.10f);
            CameraFollow2D follow = cameraObject.AddComponent<CameraFollow2D>();
            follow.Target = target;
            follow.SetWorldBounds(initialBounds);
        }

        private static void EnsureSceneInBuildSettings()
        {
            List<EditorBuildSettingsScene> scenes = new List<EditorBuildSettingsScene>(EditorBuildSettings.scenes);
            if (!scenes.Exists(s => s.path == ScenePath))
            {
                scenes.Add(new EditorBuildSettingsScene(ScenePath, true));
                EditorBuildSettings.scenes = scenes.ToArray();
            }
        }
    }
}
#endif
