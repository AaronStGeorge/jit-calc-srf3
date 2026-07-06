#include <hip/hip_runtime.h>

#include <cstdio>
#include <vector>

#include "catalog.h"

int main() {
    const int n = 1024;

    std::vector<float> a(n), b(n), c(n);
    for (int i = 0; i < n; ++i) {
        a[i] = float(i);
        b[i] = float(2 * i);
    }

    const hsaco_entry * entry = hsaco_catalog_find("vector_add");

    hipModule_t   module;
    hipFunction_t fn;
    hipModuleLoadData(&module, entry->data);
    hipModuleGetFunction(&fn, module, entry->name);

    float * d_a;
    float * d_b;
    float * d_c;
    hipMalloc(&d_a, n * sizeof(float));
    hipMalloc(&d_b, n * sizeof(float));
    hipMalloc(&d_c, n * sizeof(float));
    hipMemcpy(d_a, a.data(), n * sizeof(float), hipMemcpyHostToDevice);
    hipMemcpy(d_b, b.data(), n * sizeof(float), hipMemcpyHostToDevice);

    void * args[] = { &d_a, &d_b, &d_c, (void *) &n };
    const int block = 256;
    const int grid  = (n + block - 1) / block;
    hipModuleLaunchKernel(fn, grid, 1, 1, block, 1, 1, 0, nullptr, args, nullptr);

    hipMemcpy(c.data(), d_c, n * sizeof(float), hipMemcpyDeviceToHost);

    int errors = 0;
    for (int i = 0; i < n; ++i) {
        if (c[i] != a[i] + b[i]) {
            ++errors;
        }
    }

    printf("vector_add: %d elements, %d errors -> %s\n", n, errors, errors == 0 ? "PASS" : "FAIL");

    hipFree(d_a);
    hipFree(d_b);
    hipFree(d_c);
    hipModuleUnload(module);
    return errors == 0 ? 0 : 1;
}
