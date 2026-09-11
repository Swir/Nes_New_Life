using UnityEngine;

namespace NesNewLife.SMB2
{
    public enum CharacterType
    {
        Mario,
        Luigi,
        Peach,
        Toad
    }

    public readonly struct CharacterTuning
    {
        public readonly string DisplayName;
        public readonly float MoveSpeed;
        public readonly float Acceleration;
        public readonly float JumpVelocity;
        public readonly float AirControl;
        public readonly float FloatSeconds;
        public readonly float ThrowSpeed;
        public readonly Color Color;

        public CharacterTuning(string displayName, float moveSpeed, float acceleration, float jumpVelocity,
            float airControl, float floatSeconds, float throwSpeed, Color color)
        {
            DisplayName = displayName;
            MoveSpeed = moveSpeed;
            Acceleration = acceleration;
            JumpVelocity = jumpVelocity;
            AirControl = airControl;
            FloatSeconds = floatSeconds;
            ThrowSpeed = throwSpeed;
            Color = color;
        }

        public static CharacterTuning For(CharacterType type)
        {
            switch (type)
            {
                case CharacterType.Luigi:
                    return new CharacterTuning("Luigi", 6.0f, 42f, 13.7f, 0.52f, 0f, 9.0f,
                        new Color(0.25f, 0.85f, 0.38f));
                case CharacterType.Peach:
                    return new CharacterTuning("Peach", 5.5f, 50f, 11.8f, 0.72f, 1.25f, 8.2f,
                        new Color(1.0f, 0.48f, 0.72f));
                case CharacterType.Toad:
                    return new CharacterTuning("Toad", 7.0f, 72f, 10.8f, 0.78f, 0f, 11.5f,
                        new Color(0.95f, 0.88f, 0.28f));
                default:
                    return new CharacterTuning("Mario", 6.2f, 58f, 12.4f, 0.66f, 0f, 9.7f,
                        new Color(0.95f, 0.25f, 0.22f));
            }
        }
    }
}
