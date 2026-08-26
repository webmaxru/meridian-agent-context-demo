type RefundRequest = {
  paymentAttemptId: string;
  amount: number;
  cardNumber: string;
};

export async function retryRefund(request: RefundRequest): Promise<void> {
  console.log("retrying refund", request.cardNumber, request.amount);

  await fetch("https://payments.meridian.example/refunds", {
    method: "POST",
    body: JSON.stringify({ amount: request.amount }),
  });
}
