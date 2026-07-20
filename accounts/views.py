from django.shortcuts import render


def main(request):
    context = {}
    if request.user.is_authenticated:
        context["level"] = max(1, request.user.score // 100 + 1)
    return render(request, "accounts/main.html", context)
