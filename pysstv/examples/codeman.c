#include <stdint.h>
#include <stdio.h>

#include "codegen.c"

int main() {
	uint32_t offset, size;
	FILE *f = fopen("320x256rgb.bmp", "r");
	fseek(f, 0x02, SEEK_SET);
	fread(&size, 4, 1, f);
	fseek(f, 0x0A, SEEK_SET);
	fread(&offset, 4, 1, f);
	fseek(f, offset, SEEK_SET);

	unsigned char img[size];

	fread(img, size - offset, 1, f);
	fclose(f);

	float freqs[FREQ_COUNT], msecs[FREQ_COUNT];

	convert(img, freqs, msecs);

	for (int i = 0; i < FREQ_COUNT; i++) {
		fwrite(&(freqs[i]), 4, 1, stdout);
		fwrite(&(msecs[i]), 4, 1, stdout);
	}

	return 0;
}
