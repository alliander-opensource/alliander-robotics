// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { SignJWT } from "jose";

const textEncoder = new TextEncoder();
const JWT_VALIDITY = 3600;
const REQUIRED_ENV_VARS = ["VITE_USERID", "VITE_JWT_SECRET"];

type JwtState = {
  jwtToken: string;
  jwtError: string | null;
};

export async function generateJWT(
  device: string,
  capability: string,
): Promise<JwtState> {
  const env = import.meta.env;
  const missingEnvVars = REQUIRED_ENV_VARS.filter((name) => !env[name]);

  if (missingEnvVars.length > 0) {
    return Promise.resolve({
      jwtToken: "",
      jwtError: `Missing ${missingEnvVars.join(", ")}.`,
    });
  }

  try {
    const jwtToken = await new SignJWT({
      id: env.VITE_USERID,
      device: `d_${device}`,
      capability,
      validity: JWT_VALIDITY,
    })
      .setProtectedHeader({ alg: "HS256", typ: "JWT" })
      .setIssuedAt()
      .setExpirationTime(`${JWT_VALIDITY}s`)
      .sign(textEncoder.encode(env.VITE_JWT_SECRET!));
    return { jwtToken, jwtError: null };
  } catch (error) {
    return {
      jwtToken: "",
      jwtError:
        error instanceof Error
          ? error.message
          : "Failed to generate JWT token.",
    };
  }
}
