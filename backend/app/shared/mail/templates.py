def invitation_template(
    business_name: str,
    invitation_link: str,
):

    return f"""
    <h2>BusinessOS AI Invitation</h2>

    <p>
        You have been invited to join
        <b>{business_name}</b>.
    </p>

    <p>

        <a href="{invitation_link}">
            Accept Invitation
        </a>

    </p>
    """