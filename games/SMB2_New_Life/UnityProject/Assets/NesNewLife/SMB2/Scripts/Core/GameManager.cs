using UnityEngine;
using UnityEngine.SceneManagement;

namespace NesNewLife.SMB2
{
    public enum RunState
    {
        CharacterSelect,
        Playing,
        Paused,
        Won,
        GameOver
    }

    public sealed class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [SerializeField] private int startingLives = 3;
        [SerializeField] private CharacterType selectedCharacter = CharacterType.Mario;

        private Transform player;
        private Vector3 checkpoint;
        private int lives;
        private int score;
        private RunState state;
        private string notificationText = string.Empty;
        private float notificationUntil;

        public int Lives => lives;
        public int Score => score;
        public RunState State => state;
        public CharacterType SelectedCharacter => selectedCharacter;
        public Vector3 Checkpoint => checkpoint;
        public Transform PlayerTransform => player;
        public string NotificationText => Time.unscaledTime <= notificationUntil ? notificationText : string.Empty;
        public bool HasNotification => !string.IsNullOrEmpty(NotificationText);
        public int BestScore => CampaignSave.BestScore;
        public int Clears => CampaignSave.Clears;
        public int TotalDeaths => CampaignSave.Deaths;
        public bool HasSave => CampaignSave.HasSave;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            Instance = this;
            lives = Mathf.Max(1, startingLives);
            selectedCharacter = CampaignSave.HasSave ? CampaignSave.LastCharacter : selectedCharacter;
            state = RunState.CharacterSelect;
            Time.timeScale = 0f;

            if (GetComponent<LevelRuntimeEnhancer>() == null)
                gameObject.AddComponent<LevelRuntimeEnhancer>();
        }

        private void Start()
        {
            PlayerController2D controller = FindFirstObjectByType<PlayerController2D>();
            if (controller != null)
            {
                player = controller.transform;
                checkpoint = player.position;
                ApplyCharacter(selectedCharacter);
            }
        }

        private void Update()
        {
            if (state == RunState.CharacterSelect)
            {
                if (CampaignSave.HasSave && Input.GetKeyDown(KeyCode.C))
                {
                    StartWithCharacter(CampaignSave.LastCharacter);
                    return;
                }

                if (Input.GetKeyDown(KeyCode.N))
                {
                    CampaignSave.ResetProgress();
                    selectedCharacter = CharacterType.Mario;
                    ShowMessage("Progress reset — choose 1, 2, 3 or 4", 2f);
                    return;
                }

                if (Input.GetKeyDown(KeyCode.Alpha1)) StartWithCharacter(CharacterType.Mario);
                else if (Input.GetKeyDown(KeyCode.Alpha2)) StartWithCharacter(CharacterType.Luigi);
                else if (Input.GetKeyDown(KeyCode.Alpha3)) StartWithCharacter(CharacterType.Peach);
                else if (Input.GetKeyDown(KeyCode.Alpha4)) StartWithCharacter(CharacterType.Toad);
                return;
            }

            if (state == RunState.Playing && (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P)))
            {
                state = RunState.Paused;
                Time.timeScale = 0f;
                return;
            }

            if (state == RunState.Paused && (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P)))
            {
                state = RunState.Playing;
                Time.timeScale = 1f;
                return;
            }

            if ((state == RunState.Won || state == RunState.GameOver) && Input.GetKeyDown(KeyCode.R))
                RestartScene();
        }

        public void RegisterPlayer(Transform playerTransform)
        {
            player = playerTransform;
            checkpoint = player.position;
            ApplyCharacter(selectedCharacter);
        }

        public void StartWithCharacter(CharacterType type)
        {
            ApplyCharacter(type);
            CampaignSave.MarkStarted(type);
            state = RunState.Playing;
            Time.timeScale = 1f;
            string difficulty = CampaignSave.Clears > 0 ? $"Veteran run {CampaignSave.Clears + 1}" : "First run";
            ShowMessage($"{difficulty} — find the key and explore the sub-area", 2.6f);
        }

        public void ApplyCharacter(CharacterType type)
        {
            selectedCharacter = type;
            if (player == null)
                return;

            CharacterTuning tuning = CharacterTuning.For(type);
            PlayerController2D controller = player.GetComponent<PlayerController2D>();
            CarrySystem2D carry = player.GetComponent<CarrySystem2D>();
            SpriteRenderer renderer = player.GetComponent<SpriteRenderer>();

            if (controller != null) controller.ApplyTuning(tuning);
            if (carry != null) carry.SetThrowHorizontalSpeed(tuning.ThrowSpeed);
            if (renderer != null) renderer.color = tuning.Color;
        }

        public void ShowMessage(string text, float seconds = 1.5f)
        {
            notificationText = text ?? string.Empty;
            notificationUntil = Time.unscaledTime + Mathf.Max(0.1f, seconds);
        }

        public void AddScore(int amount)
        {
            if (state != RunState.Playing)
                return;
            score = Mathf.Max(0, score + amount);
        }

        public void SetCheckpoint(Vector3 worldPosition)
        {
            checkpoint = worldPosition;
            ShowMessage("Checkpoint reached", 1.6f);
        }

        public void PlayerDied()
        {
            if (state != RunState.Playing)
                return;

            CampaignSave.RecordDeath();
            lives--;
            if (lives <= 0)
            {
                state = RunState.GameOver;
                Time.timeScale = 0f;
                return;
            }

            RespawnPlayer();
        }

        public void RespawnPlayer()
        {
            if (player == null)
                return;

            Rigidbody2D body = player.GetComponent<Rigidbody2D>();
            if (body != null)
                body.linearVelocity = Vector2.zero;

            player.position = checkpoint;
            PlayerHealth health = player.GetComponent<PlayerHealth>();
            if (health != null)
                health.RestoreFull();

            ShowMessage($"Respawn  •  Lives: {lives}", 1.5f);
        }

        public void Win()
        {
            if (state != RunState.Playing)
                return;

            score += 5000;
            CampaignSave.RecordClear(score, selectedCharacter);
            state = RunState.Won;
            Time.timeScale = 0f;
        }

        public void RestartScene()
        {
            Time.timeScale = 1f;
            Scene active = SceneManager.GetActiveScene();
            if (active.buildIndex >= 0)
                SceneManager.LoadScene(active.buildIndex);
            else
                SceneManager.LoadScene(active.name);
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Time.timeScale = 1f;
                Instance = null;
            }
        }
    }
}
