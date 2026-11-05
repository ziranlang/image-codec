/* Test tooling only: deterministic native allocator failure, no codec bridge. */
#include "contracts.h"
#include <stddef.h>
static int calls;
void *__wrap_realloc(void *pointer, size_t bytes)
{
    (void)pointer;
    (void)bytes;
    calls++;
    return NULL;
}
int main(void) { return AllocationFailure() == 0 && calls == 1 ? 0 : 1; }
