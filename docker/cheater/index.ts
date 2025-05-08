import { OpenAI } from "openai"

const client = new OpenAI({
  apiKey: process.env.OPENAPI_KEY
});

Bun.serve({
  routes: {
    "/ask": async (request: Bun.BunRequest) => {
      const text = await request.text()
      const res = await client.chat.completions.create({
        model: "gpt-4.1-mini",
        messages: [
          {
            content: text,
            role: "user"
          }
        ]
      });

      return new Response(res.choices[0]?.message.content ?? "wtf", { status: 200 })
    },
    "/luck": () => {
      return new Response(`import numpy as np

  def solve_matrix_multiplication():
      # Read dimensions of first matrix
      n1, m1 = map(int, input().split())

      # Read elements of first matrix
      A = []
      for i in range(n1):
          row = list(map(float, input().split()))
          A.append(row)
      A = np.array(A)

      # Read dimensions of second matrix
      n2, m2 = map(int, input().split())

      # Read elements of second matrix
      B = []
      for i in range(n2):
          row = list(map(float, input().split()))
          B.append(row)
      B = np.array(B)

      # Calculate the product matrix
      C = np.matmul(A, B)

      # Print the result
      return C

  print(solve_matrix_multiplication())`);
    }
  },
  port: 3000
});
