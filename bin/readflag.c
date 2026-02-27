#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>

/*
 * SUID Binary for CTF Challenge
 *
 * Compilation (on Linux):
 *   gcc -o readflag readflag.c
 *   sudo chown root:root readflag
 *   sudo chmod 4755 readflag
 *
 * This binary allows reading /root/root.txt when executed
 * Even if called by non-root user, SUID bit makes it run as root
 */

int main(int argc, char *argv[])
{
    // Set effective UID and GID to 0 (root) - normally done by OS with SUID
    setuid(0);
    setgid(0);

    printf("Reading root flag...\n");
    printf("=================================\n");

    // Attempt to read flag file as root
    FILE *flag_file = fopen("/root/root.txt", "r");

    if (flag_file == NULL)
    {
        printf("Error: Could not open /root/root.txt\n");
        printf("Either file doesn't exist or SUID bit not set\n");
        return 1;
    }

    // Read and display flag
    char buffer[256];
    while (fgets(buffer, sizeof(buffer), flag_file) != NULL)
    {
        printf("%s", buffer);
    }

    printf("=================================\n");
    fclose(flag_file);

    return 0;
}

/*
 * Alternative version with command execution:
 *
 * #include <unistd.h>
 * #include <stdlib.h>
 *
 * int main() {
 *     setuid(0);
 *     system("cat /root/root.txt");
 *     return 0;
 * }
 */
