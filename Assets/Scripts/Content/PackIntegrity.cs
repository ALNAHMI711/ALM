using System;
using System.Security.Cryptography;
using System.Text;

namespace YOW.Content
{
    public static class PackIntegrity
    {
        public static bool VerifySha256(byte[] data, string expectedHex)
        {
            if (data == null || string.IsNullOrWhiteSpace(expectedHex))
                return false;

            using var sha = SHA256.Create();
            var actual = Convert.ToHexString(sha.ComputeHash(data));
            return string.Equals(actual, expectedHex.Trim(), StringComparison.OrdinalIgnoreCase);
        }

        public static bool VerifyUtf8(string content, string expectedHex)
        {
            return VerifySha256(Encoding.UTF8.GetBytes(content ?? string.Empty), expectedHex);
        }
    }
}
